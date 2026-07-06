import random

# 战术类型
TACTICS = {
    "正面强攻": {"attack_mod": 1.3, "defense_mod": 0.7, "morale_cost": 10, "desc": "全军突击，不计损失"},
    "稳步推进": {"attack_mod": 1.0, "defense_mod": 1.0, "morale_cost": 5, "desc": "稳扎稳打，步步为营"},
    "迂回包抄": {"attack_mod": 1.2, "defense_mod": 0.8, "morale_cost": 8, "desc": "分兵绕后，夹击敌军"},
    "据险防守": {"attack_mod": 0.7, "defense_mod": 1.4, "morale_cost": 3, "desc": "依托地形，固守待援"},
    "诱敌深入": {"attack_mod": 1.5, "defense_mod": 0.5, "morale_cost": 15, "desc": "佯败诱敌，伏兵四起"},
    "火攻": {"attack_mod": 1.4, "defense_mod": 0.6, "morale_cost": 12, "desc": "借助风势，火攻敌军"},
}

# 战术克制 (attacker -> defender: 攻击方优势倍数)
TACTIC_COUNTERS = {
    "正面强攻": {"据险防守": 0.6, "迂回包抄": 1.3},
    "稳步推进": {"正面强攻": 0.8, "诱敌深入": 1.2},
    "迂回包抄": {"据险防守": 1.4, "正面强攻": 1.1},
    "据险防守": {"正面强攻": 1.2, "火攻": 0.5},
    "诱敌深入": {"正面强攻": 1.5, "稳步推进": 0.7},
    "火攻": {"据险防守": 1.5, "迂回包抄": 0.8},
}


def calc_army_power(character, terrain_mod=None):
    """计算军团综合战力"""
    base = character.troops * (0.5 + character.training / 200)
    w_factor = character.w * 2
    morale_factor = character.morale / 50
    power = base * morale_factor + w_factor
    if terrain_mod:
        power *= terrain_mod.get("attack", 1.0)
    return max(1, int(power))


def calc_defense_power(character, city_state=None):
    """计算防守方战力（含城池驻军和城防加成）"""
    garrison = city_state.garrison if city_state else 0
    total_troops = character.troops + garrison
    base = total_troops * (0.5 + character.training / 200)
    w_factor = character.w * 2
    morale_factor = character.morale / 50
    terrain_mod = city_state.terrain_mod if city_state else {"defense": 1.0}
    power = (base * morale_factor + w_factor) * terrain_mod.get("defense", 1.0)
    return max(1, int(power))


def pick_tactic(attacker_power, defender_power, terrain, personality="balanced"):
    """根据战力和地形选择战术"""
    candidates = list(TACTICS.keys())
    scores = {}
    for name, t in TACTICS.items():
        s = t["attack_mod"] * 10
        if terrain in ("山地", "水域") and name == "据险防守":
            s += 5
        if terrain == "平原" and name in ("正面强攻", "诱敌深入"):
            s += 3
        if attacker_power > defender_power * 1.3:
            if name == "正面强攻":
                s += 4
        elif defender_power > attacker_power * 1.3:
            if name == "据险防守":
                s += 5
            if name == "诱敌深入":
                s += 3
        if personality == "aggressive":
            if name in ("正面强攻", "火攻"):
                s += 3
        elif personality == "cautious":
            if name in ("据险防守", "稳步推进"):
                s += 3
        scores[name] = s
    return max(scores, key=lambda k: scores[k])


def resolve_tactic(attack_tactic, defend_tactic):
    """计算战术对抗倍率"""
    counter = TACTIC_COUNTERS.get(attack_tactic, {}).get(defend_tactic, 1.0)
    return counter


def sim_battle(attacker, defender, city=None, world=None):
    """模拟一场完整战斗，返回 (result, logs)"""
    city_state = None
    if city and world:
        city_state = world.city_states.get(city)

    att_power = calc_army_power(attacker, city_state.terrain_mod if city_state else None)
    def_power = calc_defense_power(defender, city_state) if city else calc_army_power(defender)

    # 帝都防御加成：守方为皇帝时战力翻倍
    if city and world:
        import app.models.region as region_mod
        cs = world.city_states.get(city)
        if cs and city == region_mod.CAPITAL and cs.controller == defender.id and getattr(defender, 'is_emperor', False):
            def_power *= 2

    terrain = city_state.terrain if city_state else "平原"

    # AI选择战术
    att_tactic = pick_tactic(att_power, def_power, terrain, "aggressive")
    def_tactic = pick_tactic(def_power, att_power, terrain, "cautious")

    tactic_mod = resolve_tactic(att_tactic, def_tactic)
    effective_att = int(att_power * tactic_mod)
    total_power = effective_att + def_power
    att_ratio = effective_att / max(1, total_power)

    logs = []
    logs.append(f"{attacker.name}选择「{att_tactic}」({TACTICS[att_tactic]['desc']})")
    logs.append(f"{defender.name}选择「{def_tactic}」({TACTICS[def_tactic]['desc']})")
    logs.append(f"战术对抗倍率: {tactic_mod:.2f}")
    logs.append(f"攻击方战力: {att_power} | 防守方战力: {def_power} | 有效攻击: {effective_att}")

    # 多轮战斗 (最多5轮)
    round_num = 1
    att_troops = attacker.troops
    def_troops = defender.troops
    if city_state:
        def_troops += city_state.garrison

    battles = []
    while round_num <= 5 and att_troops > 0 and def_troops > 0:
        round_damage_att = int(att_troops * 0.1 * (1 - att_ratio))
        round_damage_def = int(def_troops * 0.1 * att_ratio)

        round_damage_att = max(1, round_damage_att)
        round_damage_def = max(1, round_damage_def)

        att_troops -= round_damage_att
        def_troops -= round_damage_def
        att_troops = max(0, att_troops)
        def_troops = max(0, def_troops)

        att_morale_loss = int(TACTICS[att_tactic]["morale_cost"] * (1 - att_ratio))
        def_morale_loss = int(TACTICS[def_tactic]["morale_cost"] * att_ratio)
        attacker.morale = max(0, attacker.morale - att_morale_loss)
        defender.morale = max(0, defender.morale - def_morale_loss)

        battles.append({
            "round": round_num,
            "att_loss": round_damage_att,
            "def_loss": round_damage_def,
            "att_troops_remaining": att_troops,
            "def_troops_remaining": def_troops,
            "att_morale": attacker.morale,
            "def_morale": defender.morale,
        })
        round_num += 1

    # 判定胜负（若5回合未分胜负，按剩余兵力比例判定）
    if att_troops <= 0 and def_troops <= 0:
        result = "draw"
        winner, loser = None, None
        logs.append("两败俱伤，双方军队全灭！")
    elif def_troops <= 0:
        result = "attacker_win"
        winner, loser = attacker, defender
        attacker.troops = int(att_troops * 0.6)
        logs.append(f"{attacker.name}攻破{defender.name}的防线！剩余兵力{int(att_troops*0.6)}")
    elif att_troops <= 0:
        result = "defender_win"
        winner, loser = defender, attacker
        defender.troops = int(def_troops * 0.6)
        logs.append(f"{defender.name}击退{attacker.name}的进攻！剩余兵力{int(def_troops*0.6)}")
    else:
        # 5回合未分胜负，按剩余兵力占比判断
        att_loss_ratio = 1 - att_troops / max(1, attacker.troops)
        def_loss_ratio = 1 - def_troops / max(1, defender.troops + (city_state.garrison if city_state else 0))
        if def_loss_ratio > att_loss_ratio * 1.2:
            result = "attacker_win"
            winner, loser = attacker, defender
            attacker.troops = int(att_troops * 0.6)
            logs.append(f"{attacker.name}突破{defender.name}的防线！剩余兵力{int(att_troops*0.6)}")
        else:
            result = "defender_win"
            winner, loser = defender, attacker
            defender.troops = int(def_troops * 0.6)
            logs.append(f"{defender.name}成功防守，{attacker.name}攻势被瓦解")

    # 战死判定
    dead = []
    for ch, final_troops, final_morale, orig_troops in [
        (attacker, att_troops, attacker.morale, attacker.troops),
        (defender, def_troops, defender.morale, defender.troops),
    ]:
        death_roll = 0
        if final_troops <= 0 and final_morale < 10:
            death_roll = 0.4
        elif orig_troops > 0 and final_troops < orig_troops * 0.3 and final_morale < 5:
            death_roll = 0.25
        if death_roll > 0 and random.random() < death_roll:
            ch.alive = False
            dead.append(ch.name)
            logs.append(f"【阵亡】{ch.name}战死沙场！")

    return {
        "result": result,
        "winner": winner.name if winner else None,
        "loser": loser.name if loser else None,
        "att_tactic": att_tactic,
        "def_tactic": def_tactic,
        "tactic_mod": round(tactic_mod, 2),
        "battles": battles,
        "att_loss": sum(b["att_loss"] for b in battles),
        "def_loss": sum(b["def_loss"] for b in battles),
        "dead": dead,
        "logs": logs,
    }
