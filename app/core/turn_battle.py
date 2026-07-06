import random
from app.core.battle import TACTICS, TACTIC_COUNTERS

TACTIC_NAMES = list(TACTICS.keys())


def resolve_tactic(attack_tactic, defend_tactic):
    counter = TACTIC_COUNTERS.get(attack_tactic, {}).get(defend_tactic, 1.0)
    return counter


def ai_pick_tactic():
    return random.choice(TACTIC_NAMES)


class TurnBattle:
    def __init__(self, player, enemy, world=None, target_city=None, task=None, ally_boost=0, is_defense=False):
        self.player = player
        self.enemy = enemy
        self.world = world
        self.target_city = target_city
        self.task = task
        self.ally_boost = ally_boost
        self.is_defense = is_defense

        self.p_tactic = None
        self.e_tactic = None
        self._counter_p_debuff = 1.0
        self._counter_e_debuff = 1.0

        self.p_hp = max(1, player.troops)
        self.p_max_hp = self.p_hp
        self.p_base_attack = max(1, int(player.w * 1.5))
        self.p_base_defense = max(1, int(player.l * 1.2))

        self.e_hp = max(1, enemy.troops)
        self.e_max_hp = self.e_hp
        self.e_base_attack = max(1, int(enemy.w * 1.5))
        self.e_base_defense = max(1, int(enemy.l * 1.2))

        # 帝都防御加成：守方为皇帝时攻防翻倍
        if world and target_city and world.city_states:
            import app.models.region as region_mod
            cs = world.city_states.get(target_city)
            if cs and target_city == region_mod.CAPITAL:
                if cs.controller == player.id and getattr(player, 'is_emperor', False):
                    self.p_base_attack *= 2
                    self.p_base_defense *= 2
                elif cs.controller == enemy.id and getattr(enemy, 'is_emperor', False):
                    self.e_base_attack *= 2
                    self.e_base_defense *= 2

        self.p_status = {}
        self.e_status = {}
        self.p_skill_cooldown = 0
        self.e_skill_cooldown = 0

        self.round = 0
        self.active = True
        self.winner = None
        self.logs = []
        self.finalized = False
        self._retreated = False
        self.garrison_pending = False
        self._p_troops_before_garrison = 0
        self._p_pre_troops = player.troops
        self._e_pre_troops = enemy.troops

    @property
    def p_attack(self):
        mod = TACTICS[self.p_tactic]["attack_mod"] if self.p_tactic else 1.0
        return max(1, int(self.p_base_attack * mod * self._counter_p_debuff))

    @property
    def p_defense(self):
        mod = TACTICS[self.p_tactic]["defense_mod"] if self.p_tactic else 1.0
        return max(1, int(self.p_base_defense * mod * self._counter_p_debuff))

    @property
    def e_attack(self):
        mod = TACTICS[self.e_tactic]["attack_mod"] if self.e_tactic else 1.0
        return max(1, int(self.e_base_attack * mod * self._counter_e_debuff))

    @property
    def e_defense(self):
        mod = TACTICS[self.e_tactic]["defense_mod"] if self.e_tactic else 1.0
        return max(1, int(self.e_base_defense * mod * self._counter_e_debuff))

    def set_tactics(self, p_tactic, e_tactic=None):
        self.p_tactic = p_tactic
        self.e_tactic = e_tactic or ai_pick_tactic()
        self._compute_counter()
        self.logs.append(f"{self.player.name}选择「{self.p_tactic}」({TACTICS[self.p_tactic]['desc']})")
        self.logs.append(f"{self.enemy.name}选择「{self.e_tactic}」({TACTICS[self.e_tactic]['desc']})")
        if self._counter_p_debuff < 1.0:
            self.logs.append(f"战术被克制，{self.player.name}攻击防御小幅下降！")
        elif self._counter_e_debuff < 1.0:
            self.logs.append(f"战术克制敌方，{self.enemy.name}被压制！")

    def _compute_counter(self):
        p_mod = resolve_tactic(self.p_tactic, self.e_tactic)
        e_mod = resolve_tactic(self.e_tactic, self.p_tactic)
        self._counter_p_debuff = min(1.0, p_mod / 0.85) if p_mod < 0.9 else 1.0
        self._counter_e_debuff = min(1.0, e_mod / 0.85) if e_mod < 0.9 else 1.0

    def to_dict(self):
        return {
            "active": self.active,
            "round": self.round,
            "winner": self.winner.name if self.winner else None,
            "p_name": self.player.name,
            "e_name": self.enemy.name,
            "p_hp": self.p_hp,
            "p_max_hp": self.p_max_hp,
            "p_attack": self.p_attack,
            "p_defense": self.p_defense,
            "p_status": dict(self.p_status),
            "p_skill": self.player.skill,
            "p_tactic": self.p_tactic,
            "e_hp": self.e_hp,
            "e_max_hp": self.e_max_hp,
            "e_attack": self.e_attack,
            "e_defense": self.e_defense,
            "e_status": dict(self.e_status),
            "e_skill": self.enemy.skill,
            "e_tactic": self.e_tactic,
            "logs": self.logs[-5:],
            "tactics_open": self.p_tactic is None,
            "garrison_pending": self.garrison_pending,
            "p_troops": self._p_troops_before_garrison or int(self.p_hp),
            "tactic_list": TACTIC_NAMES,
            "is_defense": self.is_defense,
            "p_skill_cooldown": self.p_skill_cooldown,
            "e_skill_cooldown": self.e_skill_cooldown,
        }

    def process_action(self, player_action):
        self.round += 1
        round_log = []

        self._tick_status(self.p_status)
        self._tick_status(self.e_status)
        if self.p_skill_cooldown > 0:
            self.p_skill_cooldown -= 1
        if self.e_skill_cooldown > 0:
            self.e_skill_cooldown -= 1

        # Save pre-round HP for garrison calculation
        pre_p_hp = int(self.p_hp)
        pre_e_hp = int(self.e_hp)

        e_action = self._ai_decision()

        p_defending = False
        e_defending = False

        p_log_lines = []
        if "stun" in self.p_status and self.p_status["stun"] > 0:
            p_log_lines.append(f"{self.player.name}被禁锢，无法行动！")
        else:
            if player_action == "attack":
                dmg = self._calc_damage(self.p_attack, self.e_defense, self.e_hp)
                if e_defending:
                    dmg = int(dmg * 0.5)
                dmg = max(1, dmg)
                self.e_hp = max(0, self.e_hp - dmg)
                p_log_lines.append(f"{self.player.name}攻击，造成 {dmg} 点伤害")
            elif player_action == "defend":
                p_defending = True
                p_log_lines.append(f"{self.player.name}进入防御姿态")
            elif player_action == "skill":
                if "silence" in self.p_status and self.p_status["silence"] > 0:
                    p_log_lines.append(f"{self.player.name}被沉默，无法使用技能！")
                elif self.p_skill_cooldown > 0:
                    p_log_lines.append(f"{self.player.name}技能冷却中（剩{self.p_skill_cooldown}回合）")
                else:
                    skill_lines = self._use_skill(self.player, self.enemy, self.p_status, self.e_status, is_player=True)
                    p_log_lines.extend(skill_lines)
                    self.p_skill_cooldown = 2

        e_log_lines = []
        if "stun" in self.e_status and self.e_status["stun"] > 0:
            e_log_lines.append(f"{self.enemy.name}被禁锢，无法行动！")
        else:
            if e_action == "attack":
                dmg = self._calc_damage(self.e_attack, self.p_defense, self.p_hp)
                if p_defending:
                    dmg = int(dmg * 0.5)
                dmg = max(1, dmg)
                self.p_hp = max(0, self.p_hp - dmg)
                e_log_lines.append(f"{self.enemy.name}攻击，造成 {dmg} 点伤害")
            elif e_action == "defend":
                e_defending = True
                e_log_lines.append(f"{self.enemy.name}进入防御姿态")
            elif e_action == "skill":
                if "silence" in self.e_status and self.e_status["silence"] > 0:
                    e_log_lines.append(f"{self.enemy.name}被沉默，无法使用技能！")
                elif self.e_skill_cooldown > 0:
                    e_log_lines.append(f"{self.enemy.name}技能冷却中（剩{self.e_skill_cooldown}回合）")
                else:
                    skill_lines = self._use_skill(self.enemy, self.player, self.e_status, self.p_status, is_player=False)
                    e_log_lines.extend(skill_lines)
                    self.e_skill_cooldown = 2

        round_log.extend(p_log_lines)
        round_log.extend(e_log_lines)

        if e_action == "retreat":
            self.active = False
            self.winner = self.player
            round_log.append(f"{self.enemy.name}撤退了")
            self.logs.extend(round_log)
            if self.is_defense:
                self.player.morale = min(100, self.player.morale + self._morale_change(15))
                self.enemy.morale = max(0, self.enemy.morale - 15)
                self._finalize()
            else:
                if self._p_troops_before_garrison <= 0:
                    self._p_troops_before_garrison = max(1, pre_p_hp)
                self.garrison_pending = True
                self.player.morale = min(100, self.player.morale + self._morale_change(15))
                self.enemy.morale = max(0, self.enemy.morale - 15)
                self.logs.extend(round_log)
            return self.to_dict()

        if player_action == "retreat":
            self.active = False
            self.winner = None
            self._retreated = True
            round_log.append(f"{self.player.name}撤退了")
            self.logs.extend(round_log)
            self._finalize()
            return self.to_dict()

        if self.p_hp <= 0 or self.e_hp <= 0:
            if self.p_hp <= 0 and self.e_hp <= 0:
                self.active = False
                self.winner = None
                round_log.append("两败俱伤！")
                self._finalize()
            elif self.e_hp <= 0:
                self.winner = self.player
                self.active = False
                if self.is_defense:
                    round_log.append(f"{self.player.name}成功防守{self.target_city}！")
                    self.player.morale = min(100, self.player.morale + self._morale_change(15))
                    self.enemy.morale = max(0, self.enemy.morale - 15)
                    self._finalize()
                else:
                    round_log.append(f"{self.player.name}击败了{self.enemy.name}！")
                    if self._p_troops_before_garrison <= 0:
                        self._p_troops_before_garrison = max(1, pre_p_hp)
                    self.garrison_pending = True
                    self.player.morale = min(100, self.player.morale + self._morale_change(15))
                    self.enemy.morale = max(0, self.enemy.morale - 15)
            else:
                self.active = False
                self.winner = self.enemy
                round_log.append(f"{self.enemy.name}击败了{self.player.name}！")
                self._finalize()

        self.logs.extend(round_log)
        return self.to_dict()

    def _calc_damage(self, attack, defense, target_hp):
        ratio = max(0.3, attack / max(1, defense))
        base_pct = 0.06 * ratio
        return max(1, int(target_hp * base_pct * random.uniform(0.8, 1.2)))

    def _use_skill(self, caster, target, caster_status, target_status, is_player):
        skill = caster.skill
        lines = []
        skill_power = caster.p

        if skill["type"] == "damage":
            target_hp = self.e_hp if is_player else self.p_hp
            ratio = max(0.3, skill_power * 2 / max(1, target.l * 1.2))
            base_pct = 0.25 * ratio
            dmg = max(1, int(target_hp * base_pct * random.uniform(1.0, 1.5)))
            target_hp_attr = "p_hp" if is_player else "e_hp"
            setattr(self, target_hp_attr, max(0, getattr(self, target_hp_attr) - dmg))
            lines.append(f"{caster.name}施展「{skill['name']}」，造成 {dmg} 点伤害")

        elif skill["type"] == "silence":
            chance = skill_power / 200
            if random.random() < chance:
                target_status["silence"] = 2
                lines.append(f"{caster.name}施展「{skill['name']}」，{target.name}被沉默！")
            else:
                lines.append(f"{caster.name}施展「{skill['name']}」但未能命中")

        elif skill["type"] == "stun":
            chance = skill_power / 200
            if random.random() < chance:
                target_status["stun"] = 1
                lines.append(f"{caster.name}施展「{skill['name']}」，{target.name}被禁锢！")
            else:
                lines.append(f"{caster.name}施展「{skill['name']}」但未能命中")

        return lines

    def _tick_status(self, status):
        for k in list(status.keys()):
            status[k] -= 1
            if status[k] <= 0:
                del status[k]

    def _ai_decision(self):
        if self.e_hp < 500 and random.random() < 0.4:
            return "retreat"
        r = random.random()
        if r < 0.55:
            return "attack"
        elif r < 0.75:
            return "defend"
        else:
            return "skill"

    def _morale_change(self, base):
        charm = self.player.i
        return base + int(charm * 0.1)

    def set_garrison(self, garrison):
        if not self.garrison_pending:
            return self.to_dict()
        p = self.player
        e = self.enemy
        p.troops = max(1, int(self._p_troops_before_garrison - garrison))
        e.troops = max(1, int(self.e_hp))
        if self.ally_boost > 0:
            e.troops = max(0, e.troops - self.ally_boost)

        if self.world and self.target_city:
            cs = self.world.city_states.get(self.target_city)
            if cs:
                cs.garrison += garrison
                old_controller = cs.controller
                if old_controller and old_controller != p.id:
                    old_char = self.world.characters.get(old_controller)
                    if old_char and self.target_city in old_char.controlled_cities:
                        old_char.controlled_cities.remove(self.target_city)
                cs.controller = p.id
                if self.target_city not in p.controlled_cities:
                    p.controlled_cities.append(self.target_city)

        self.world._emit({
            "type": "battle",
            "desc": f"{p.name}攻占{self.target_city}！留守{garrison}兵力",
            "battle_result": {"result": "attacker_win", "logs": self.logs},
        })

        self.garrison_pending = False
        self.logs.append(f"{p.name}在{self.target_city}留守{garrison}兵力")
        if self.world:
            self.world.active_battle = None
        return self.to_dict()

    def _finalize(self):
        if self.finalized:
            return
        self.finalized = True
        if self.world:
            self.world.active_battle = None
        if not self.world:
            return

        p = self.player
        e = self.enemy

        p.troops = max(1, int(self.p_hp))
        e.troops = max(1, int(self.e_hp))
        if self.ally_boost > 0:
            if self.winner == self.player or self.winner is None:
                e.troops = max(0, e.troops - self.ally_boost)

        if getattr(self, '_retreated', False):
            p.troops = max(1, int(self.p_hp * 0.6))
            p.morale = max(0, p.morale - self._morale_change(15))
            e.morale = min(100, e.morale + 10)
            if self.is_defense:
                from app.core.economy import conquer_city
                conquer_city(self.world, e, self.target_city, None)
                self.world._emit({
                    "type": "battle",
                    "desc": f"{p.name}弃守{self.target_city}，{e.name}占领该城",
                    "battle_result": {"result": "attacker_win", "logs": self.logs},
                })
            else:
                self.world._emit({
                    "type": "battle",
                    "desc": f"{p.name}从{self.target_city}撤退",
                    "battle_result": {"result": "retreat", "logs": self.logs},
                })
        elif self.winner == self.player and not self.garrison_pending:
            if self.is_defense:
                p.morale = min(100, p.morale)
                e.morale = max(0, e.morale)
                self.world._emit({
                    "type": "battle",
                    "desc": f"{p.name}成功防守{self.target_city}，击退{e.name}！",
                    "battle_result": {"result": "defender_win", "logs": self.logs},
                })
            elif self.target_city:
                from app.core.economy import conquer_city
                conquer_city(self.world, p, self.target_city, {
                    "result": "attacker_win",
                    "logs": self.logs,
                })
        elif self.winner == self.enemy:
            p.morale = max(0, p.morale - self._morale_change(15))
            e.morale = min(100, e.morale + 15)
            p.troops = max(1, int(self.p_hp * 0.3))
            if self.is_defense:
                from app.core.economy import conquer_city
                conquer_city(self.world, e, self.target_city, {
                    "result": "attacker_win",
                    "logs": self.logs,
                })
            death_roll = 0.4 if self.p_hp <= 0 else 0.25
            if random.random() < death_roll:
                p.alive = False
                self.world.game_over = True
                self.world._emit({
                    "type": "death",
                    "desc": f"{p.name}在战斗中阵亡！",
                })
            if self.is_defense:
                self.world._emit({
                    "type": "battle",
                    "desc": f"{e.name}攻破{self.target_city}，{p.name}被击败！",
                    "battle_result": {"result": "attacker_win", "logs": self.logs},
                })
            else:
                self.world._emit({
                    "type": "battle",
                    "desc": f"{p.name}攻打{self.target_city}失败（vs {e.name}）",
                    "battle_result": {"result": "defender_win", "logs": self.logs},
                })
        else:
            p.morale = max(0, p.morale - self._morale_change(5))
            e.morale = max(0, e.morale - 5)
            p.troops = max(1, int(self.p_hp * 0.3))
            e.troops = max(1, int(self.e_hp * 0.3))
            if self.is_defense:
                self.world._emit({
                    "type": "battle",
                    "desc": f"{p.name}防守{self.target_city}，与{e.name}两败俱伤！",
                    "battle_result": {"result": "draw", "logs": self.logs},
                })
            else:
                self.world._emit({
                    "type": "battle",
                    "desc": f"{p.name}与{e.name}两败俱伤！",
                    "battle_result": {"result": "draw", "logs": self.logs},
                })

        # 战后恢复：损失兵力恢复10%-30%，消耗金钱
        for ch, pre, final in [(p, self._p_pre_troops, p.troops), (e, self._e_pre_troops, e.troops)]:
            lost = max(0, pre - final)
            if lost <= 0:
                continue
            gold = getattr(ch, 'gold', 0)
            rate = min(0.3, 0.1 + gold / 5000)
            recovered = int(lost * rate)
            cost = int(recovered * 1.5)
            if gold >= cost and recovered > 0:
                ch.gold = gold - cost
                ch.troops += recovered
                self.logs.append(f"{ch.name}战后恢复{recovered}兵力，消耗{cost}金")
