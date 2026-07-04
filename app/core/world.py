import os
import random
from collections import defaultdict
from app.models.character import Character

STAT_FIELDS = ["base_l", "base_w", "base_i", "base_p"]
STAT_LABELS = {"base_l":"机敏","base_w":"武力","base_i":"魅力","base_p":"智谋"}


def _load_json(name):
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", name)
    if not os.path.isfile(path):
        return []
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


DATA = _load_json("chars.json")
TREASURES = _load_json("treasures.json")

NON_CHAR_TASKS = [
    {"name":"深山探宝","desc":"深入险山寻找前代高人遗宝","diff":50,"stat":"l","tag":"non_char"},
    {"name":"采集灵药","desc":"在绝壁悬崖采集珍贵药材","diff":40,"stat":"l","tag":"non_char"},
    {"name":"暗夜侦察","desc":"潜入关键地点探查情报","diff":55,"stat":"l","tag":"non_char"},
    {"name":"追捕凶犯","desc":"追捕流窜作恶的江湖凶犯","diff":60,"stat":"w","tag":"non_char"},
    {"name":"破解机关","desc":"探索古墓破解机关禁制","diff":50,"stat":"l","tag":"non_char"},
]

CHAR_TASKS = [
    {"name":"结交侠士","desc":"拜访名门大派结交江湖侠士","diff":45,"stat":"i","tag":"char"},
    {"name":"化解恩怨","desc":"调解两个门派之间的恩怨","diff":55,"stat":"i","tag":"char"},
    {"name":"说服掌门","desc":"说服一门掌门支持正义之举","diff":60,"stat":"i","tag":"char"},
    {"name":"招募人才","desc":"招募隐居山野的奇人异士","diff":50,"stat":"i","tag":"char"},
    {"name":"调解纠纷","desc":"处理江湖帮派之间的纠纷","diff":45,"stat":"i","tag":"char"},
]

DEADLY_TASKS = [
    {"name":"独闯龙潭","desc":"深入龙潭虎穴，九死一生","diff":70,"stat":"w","tag":"deadly"},
    {"name":"刺杀魔头","desc":"暗杀江湖第一魔头","diff":75,"stat":"l","tag":"deadly"},
    {"name":"破解绝阵","desc":"破解上古绝命阵法，稍有不慎万劫不复","diff":65,"stat":"p","tag":"deadly"},
    {"name":"单挑群雄","desc":"以一己之力挑战江湖群雄","diff":70,"stat":"w","tag":"deadly"},
    {"name":"盗取至宝","desc":"从戒备森严之地盗取至宝","diff":65,"stat":"l","tag":"deadly"},
]

COOP_TASKS = [
    {"name":"联手对敌","desc":"与{target}联手对抗外敌","diff":50,"stat":"w","tag":"coop"},
    {"name":"共商大计","desc":"与{target}共同谋划大事","diff":45,"stat":"i","tag":"coop"},
    {"name":"切磋武艺","desc":"与{target}切磋武艺交流心得","diff":55,"stat":"w","tag":"coop"},
    {"name":"结伴游历","desc":"与{target}结伴游历江湖","diff":40,"stat":"i","tag":"coop"},
    {"name":"联手寻宝","desc":"与{target}联手寻找宝藏","diff":50,"stat":"l","tag":"coop"},
]

WUXIA_EVENTS = [
    "路遇高人指点，{name}武功精进", "夜观天象，{name}悟得新招",
    "山中遇隐士论道，{name}内力大增", "市井见不平事，{name}仗义出手赢得名声",
    "偶遇奇人传授心法，{name}内力提升", "于瀑布下练功，{name}领悟流水之意",
    "梦中得仙人传授，{name}功力大进", "于古庙中发现前人武学心得",
    "茶馆听闻江湖秘闻，{name}见识增长", "助人为乐，受高人点拨",
]


class World:
    def __init__(self):
        self.characters = {}
        self.rel = defaultdict(dict)
        self.next_id = 0

        self.player_char = None
        self.triggers = {"apprentice": False, "marry": False, "sworn": False}
        self.used_treasures = set()
        self.pending_tasks = []
        self.task_next_id = 0
        self.pending_decay = None
        self.tournament = None
        self.game_over = False

        for d in DATA:
            self.create(d["gender"], d["name"], d["l"], d["w"], d["i"], d["p"], d.get("desc", ""), d.get("age", 20))

    def create(self, gender, name, l, w, i, p, desc="", age=20):
        c = Character(self.next_id, name, gender, l, w, i, p, desc, age)
        self.characters[self.next_id] = c

        for k in self.characters:
            if k != self.next_id:
                v = random.randint(-20, 20)
                self.rel[k][self.next_id] = v
                self.rel[self.next_id][k] = v

        self.next_id += 1

    def alive(self):
        return [c for c in self.characters.values() if c.alive]

    def alive_except_player(self):
        return [c for c in self.characters.values() if c.alive and c != self.player_char]

    def get(self, name):
        for c in self.characters.values():
            if c.name == name:
                return c

    def random_alive(self, n):
        pool = self.alive_except_player()
        random.shuffle(pool)
        return pool[:n]

    def start_candidates(self):
        return random.sample(list(self.characters.values()), min(3, len(self.characters)))

    def apprentice_candidates(self):
        if not self.player_char or self.triggers["apprentice"]:
            return []
        pool = [c for c in self.alive_except_player()
                if c.age > self.player_char.age and not c.master
                and self.rel[self.player_char.id].get(c.id, 0) >= 60]
        if len(pool) < 3:
            return []
        random.shuffle(pool)
        return pool[:3]

    def marry_candidates(self):
        if not self.player_char or self.triggers["marry"]:
            return []
        pool = [c for c in self.alive_except_player()
                if c.gender != self.player_char.gender and not c.spouse
                and self.rel[self.player_char.id].get(c.id, 0) >= 60]
        if len(pool) < 3:
            return []
        random.shuffle(pool)
        return pool[:3]

    def sworn_candidates(self):
        if not self.player_char or self.triggers["sworn"]:
            return []
        pool = [c for c in self.alive_except_player()
                if self.rel[self.player_char.id].get(c.id, 0) >= 60]
        if len(pool) < 3:
            return []
        random.shuffle(pool)
        return pool[:3]

    def export(self):
        rel = self.rel[self.player_char.id] if self.player_char and self.player_char.id in self.rel else {}
        return {
            "round": getattr(self, "engine", None) and self.engine.round or 0,
            "player": self.player_char.to_dict() if self.player_char else None,
            "triggers": self.triggers,
            "characters": [{**c.to_dict(), "rel": rel.get(c.id, 0)} for c in self.alive()],
            "game_over": self.game_over,
        }

    def set_player(self, name):
        c = self.get(name)
        if c:
            self.player_char = c
        return self.player_char

    def _emit(self, evt):
        bus = getattr(self, "engine", None)
        if bus:
            bus.bus.emit(evt)

    def do_apprentice(self, target_name):
        target = self.get(target_name)
        if target and self.player_char:
            self.player_char.master = target_name
            self.triggers["apprentice"] = True
            self._emit({"type": "apprentice", "desc": f"{self.player_char.name}拜师{target_name}"})

    def do_marry(self, target_name):
        target = self.get(target_name)
        if target and self.player_char:
            self.player_char.spouse = target_name
            target.spouse = self.player_char.name
            self.triggers["marry"] = True
            self._emit({"type": "marry", "desc": f"{self.player_char.name}与{target_name}结为夫妻"})

    def do_sworn(self, target_name):
        target = self.get(target_name)
        if target and self.player_char:
            elder, younger = (self.player_char, target) if self.player_char.age > target.age else (target, self.player_char)
            elder.sworn_brothers.append(younger.name)
            younger.sworn_brothers.append(elder.name)
            self.triggers["sworn"] = True
            label = "兄弟" if elder.gender == "男" else "姐妹"
            self._emit({"type": "sworn", "desc": f"{elder.name}与{younger.name}结为{label}"})

    def random_wuxia_event(self):
        chars = self.alive()
        if not chars:
            return
        c = random.choice(chars)
        templ = random.choice(WUXIA_EVENTS)
        desc = templ.format(name=c.name)
        self._emit({"type": "wuxia", "desc": desc})

    def _grant_treasure(self, char, t):
        """授予宝物，同类别旧宝物被替换（移除旧加成，添加新加成）"""
        old = next((x for x in char.treasures if x["type"] == t["type"]), None)
        if old:
            for k in ("l", "w", "i", "p"):
                setattr(char, f"bonus_{k}", getattr(char, f"bonus_{k}") - old.get(k, 0))
            char.treasures.remove(old)
        for k in ("l", "w", "i", "p"):
            setattr(char, f"bonus_{k}", getattr(char, f"bonus_{k}") + t.get(k, 0))
        char.treasures.append(t)

    def random_treasure_event(self):
        if not TREASURES or not self.player_char:
            return
        available = [t for t in TREASURES if t["id"] not in self.used_treasures]
        if not available:
            return
        t = random.choice(available)
        self.used_treasures.add(t["id"])
        self._grant_treasure(self.player_char, t)
        self._emit({"type": "treasure", "desc": f"{self.player_char.name}奇遇获得【{t['name']}】（{t['type']}）：{t['desc']}"})

    def character_treasure_event(self):
        if not TREASURES:
            return
        available = [t for t in TREASURES if t["id"] not in self.used_treasures]
        if not available:
            return
        chars = self.alive_except_player()
        if not chars:
            return
        c = random.choice(chars)
        t = random.choice(available)
        self.used_treasures.add(t["id"])
        self._grant_treasure(c, t)
        self._emit({"type": "treasure", "desc": f"{c.name}在江湖游历中获得【{t['name']}】"})

    # ---- 任务系统 ----

    def generate_tasks(self):
        self.pending_tasks = []
        pool = NON_CHAR_TASKS + CHAR_TASKS + COOP_TASKS
        # 概率出现极难任务
        if random.random() < 0.3:
            pool = pool + DEADLY_TASKS
        count = random.randint(1, 2)
        selected = random.sample(pool, min(count, len(pool)))
        for t in selected:
            entry = {
                "id": self.task_next_id,
                "name": t["name"],
                "desc": t["desc"],
                "type": t["tag"],
                "stat": t["stat"],
                "difficulty": t["diff"],
            }
            if t["tag"] == "coop":
                targets = self.alive_except_player()
                if not targets:
                    continue
                target = random.choice(targets)
                entry["target"] = target.name
                entry["desc"] = t["desc"].format(target=target.name)
            self.pending_tasks.append(entry)
            self.task_next_id += 1

    def pending_task_data(self):
        if not self.player_char:
            return []
        result = []
        for t in self.pending_tasks:
            stat_val = getattr(self.player_char, t["stat"])
            base_chance = min(95, max(5, 50 + (stat_val - t["difficulty"]) * 0.5))
            focus_chance = min(95, max(5, 50 + (stat_val - t["difficulty"]) * 0.75))
            scheme_bonus = int(self.player_char.p * 0.1)
            result.append({
                "id": t["id"],
                "name": t["name"],
                "desc": t["desc"],
                "type": t["type"],
                "target": t.get("target", None),
                "difficulty": t["difficulty"],
                "deadly": t["type"] == "deadly",
                "base_chance": int(base_chance),
                "focus_chance": int(focus_chance),
                "scheme_bonus": scheme_bonus,
                "chance_with_scheme": min(95, int(base_chance + scheme_bonus)),
            })
        return result

    def execute_task(self, task_id, mode="normal"):
        task = next((t for t in self.pending_tasks if t["id"] == task_id), None)
        if not task or not self.player_char:
            return {"success": False, "desc": "任务不存在"}
        stat_val = getattr(self.player_char, task["stat"])
        if mode == "focus":
            chance = min(95, max(5, 50 + (stat_val - task["difficulty"]) * 0.75))
        else:
            base = min(95, max(5, 50 + (stat_val - task["difficulty"]) * 0.5))
            chance = base + (self.player_char.p * 0.1 if mode == "scheme" else 0)
            chance = min(95, max(5, chance))
        roll = random.randint(1, 100)
        success = roll <= chance
        self.pending_tasks = []
        desc_parts = [f"{self.player_char.name}执行「{task['name']}」"]
        mode_labels = {"scheme":"（运用智谋辅助）", "focus":"（全力施展）"}
        if mode in mode_labels:
            desc_parts.append(mode_labels[mode])
        desc_parts.append("，")
        xia_yi_gain = random.randint(2, 5) if success else 0
        if success:
            if task["type"] == "coop" and task.get("target"):
                target = self.get(task["target"])
                if target:
                    change = random.randint(10, 20)
                    self.rel[self.player_char.id][target.id] += change
                    self.rel[target.id][self.player_char.id] += change
                    self.player_char.xia_yi += xia_yi_gain
                    desc_parts.append(f"成功！与{target.name}好感度+{change}，侠义值+{xia_yi_gain}")
                    self._emit({"type": "task_success", "desc": "".join(desc_parts)})
                    return {"success": True, "desc": "".join(desc_parts), "rel_change": change, "xia_yi": xia_yi_gain}
            is_deadly = task["type"] == "deadly"
            reward = self._grant_task_reward(deadly=is_deadly)
            xia_yi_gain = random.randint(3, 6) if is_deadly else xia_yi_gain
            self.player_char.xia_yi += xia_yi_gain
            desc_parts.append(f"成功！{reward['desc']}，侠义值+{xia_yi_gain}")
            self._emit({"type": "task_success", "desc": "".join(desc_parts)})
            return {"success": True, "desc": "".join(desc_parts), "reward": reward, "xia_yi": xia_yi_gain}
        else:
            if task["type"] == "coop" and task.get("target"):
                target = self.get(task["target"])
                if target:
                    change = -random.randint(5, 10)
                    self.rel[self.player_char.id][target.id] += change
                    self.rel[target.id][self.player_char.id] += change
                    desc_parts.append(f"失败！与{target.name}好感度{change}")
                    self._emit({"type": "task_fail", "desc": "".join(desc_parts)})
                    return {"success": False, "desc": "".join(desc_parts), "rel_change": change}
            if task["type"] == "deadly":
                death_chance = max(0.1, min(0.5, (task["difficulty"] - stat_val) / 100))
                if random.random() < death_chance:
                    self.player_char.alive = False
                    self.game_over = True
                    desc_parts.append(f"失败！{self.player_char.name}在任务中不幸身亡！")
                    self._emit({"type": "death", "desc": "".join(desc_parts)})
                    return {"success": False, "desc": "".join(desc_parts), "game_over": True}
            penalty = self._apply_task_penalty()
            desc_parts.append(f"失败！{penalty['desc']}")
            self._emit({"type": "task_fail", "desc": "".join(desc_parts)})
            return {"success": False, "desc": "".join(desc_parts), "penalty": penalty}

    def _grant_task_reward(self, deadly=False):
        stats = ["bonus_l", "bonus_w", "bonus_i", "bonus_p"]
        stat = random.choice(stats)
        boost = random.randint(3, 5) if deadly else random.randint(1, 3)
        setattr(self.player_char, stat, getattr(self.player_char, stat) + boost)
        label = {"bonus_l":"机敏","bonus_w":"武力","bonus_i":"魅力","bonus_p":"智谋"}[stat]
        return {"type": "stat", "stat": stat, "value": boost, "desc": f"{label}+{boost}"}

    def _apply_task_penalty(self):
        stats = ["bonus_l", "bonus_w", "bonus_i", "bonus_p"]
        stat = random.choice(stats)
        penalty = -random.randint(1, 2)
        setattr(self.player_char, stat, getattr(self.player_char, stat) + penalty)
        label = {"bonus_l":"机敏","bonus_w":"武力","bonus_i":"魅力","bonus_p":"智谋"}[stat]
        return {"type": "stat", "value": penalty, "desc": f"{label}{penalty}"}

    # ---- 战斗（不和引起） ----

    def combat_event(self):
        chars_by_region = defaultdict(list)
        for c in self.alive():
            chars_by_region[c.region].append(c)
        candidates = []
        for region, chars in chars_by_region.items():
            for i in range(len(chars)):
                for j in range(i+1, len(chars)):
                    ca, cb = chars[i], chars[j]
                    rel = self.rel[ca.id].get(cb.id, 0)
                    if rel < -10:
                        candidates.append((ca, cb, region))
        if not candidates:
            return
        random.shuffle(candidates)
        a, b, region = candidates[0]
        aw, bw = a.w, b.w
        if aw >= bw:
            winner, loser = a, b
        else:
            winner, loser = b, a
        loser.bonus_w = max(0, loser.bonus_w - random.randint(1, 3))
        winner.bonus_w += random.randint(0, 2)
        # 死亡判定：武力差距越大越可能死亡
        gap = winner.w - loser.w
        death_chance = max(0.05, min(0.5, gap / 100))
        desc = f"【{region}】{winner.name}与{loser.name}不和激化，爆发战斗！{winner.name}胜出，{loser.name}武力受损"
        if random.random() < death_chance:
            loser.alive = False
            desc += f"，{loser.name}伤重身亡！"
            if loser == self.player_char:
                self.game_over = True
            self._emit({"type": "death", "desc": desc})
            return
        self._emit({"type": "combat", "desc": desc})

    # ---- 和睦（引起任务共享） ----

    def cooperation_event(self):
        chars_by_region = defaultdict(list)
        for c in self.alive():
            chars_by_region[c.region].append(c)
        candidates = []
        for region, chars in chars_by_region.items():
            for i in range(len(chars)):
                for j in range(i+1, len(chars)):
                    ca, cb = chars[i], chars[j]
                    rel = self.rel[ca.id].get(cb.id, 0)
                    if rel > 10:
                        candidates.append((ca, cb, region))
        if not candidates:
            return
        random.shuffle(candidates)
        a, b, region = candidates[0]
        stats = ["bonus_l", "bonus_w", "bonus_i", "bonus_p"]
        for c in (a, b):
            s = random.choice(stats)
            boost = random.randint(1, 2)
            setattr(c, s, getattr(c, s) + boost)
        self._emit({
            "type": "cooperation",
            "desc": f"【{region}】{a.name}与{b.name}和睦互助，共享江湖情报，二人各有所获"
        })

    def do_tick_events(self):
        self.random_wuxia_event()
        if random.random() < 0.3 and self.player_char:
            self.random_treasure_event()
        if random.random() < 0.2:
            self.character_treasure_event()

    # ---- 不进则退（每10回合） ----

    def check_decay(self):
        if not getattr(self, "engine", None) or self.engine.round % 10 != 0:
            return
        # NPC自动衰减
        for c in self.alive_except_player():
            f = random.choice(STAT_FIELDS)
            old = getattr(c, f)
            new = int(old * 0.9)
            setattr(c, f, new)
            self._emit({"type": "decay", "desc": f"{c.name}不进则退，{STAT_LABELS[f]}从{old}降至{new}"})
        # 玩家选择
        if self.player_char:
            stats = [{"label": STAT_LABELS[f], "field": f, "value": getattr(self.player_char, f)} for f in STAT_FIELDS]
            self.pending_decay = {"stats": stats}

    def execute_decay(self, field):
        if not self.pending_decay or not self.player_char:
            return {"ok": False}
        old = getattr(self.player_char, field)
        new = int(old * 0.9)
        setattr(self.player_char, field, new)
        self._emit({"type": "decay", "desc": f"{self.player_char.name}不进则退，选择降低{STAT_LABELS[field]}：{old}→{new}"})
        self.pending_decay = None
        return {"ok": True, "field": field, "old": old, "new": new}

    # ---- 天下第一武道会（每30回合） ----

    def _tournament_fight(self, a, b):
        ra, rb = a.w + random.randint(-10, 10), b.w + random.randint(-10, 10)
        return (a, b) if ra >= rb else (b, a)

    def maybe_start_tournament(self):
        if not getattr(self, "engine", None) or self.engine.round % 30 != 0:
            return
        chars = sorted(self.alive(), key=lambda c: c.xia_yi, reverse=True)[:16]
        if len(chars) < 4:
            self._emit({"type": "tournament", "desc": "天下第一武道会参与者不足，取消举办"})
            return
        # 调整人数为4的倍数，确保每组人数相等
        chars = chars[:len(chars) - len(chars) % 4]
        random.shuffle(chars)
        group_names = ["甲", "乙", "丙", "丁"]
        group_size = len(chars) // 4
        groups = [{"name": group_names[gi], "players": chars[gi*group_size:(gi+1)*group_size]} for gi in range(4)]
        self._emit({"type": "tournament", "desc": f"天下第一武道会开幕！{len(chars)}名高手齐聚一堂"})

        group_winners, group_runners = [], []
        for g in groups:
            players = g["players"]
            random.shuffle(players)
            m = []
            # 第一轮：随机配对
            w1, l1 = self._tournament_fight(players[0], players[1])
            w2, l2 = self._tournament_fight(players[2], players[3])
            m.append({"round":"第一轮","a":players[0].name,"b":players[1].name,"winner":w1.name})
            m.append({"round":"第一轮","a":players[2].name,"b":players[3].name,"winner":w2.name})
            # 胜者组决赛 → 小组第一出线
            wf_w, wf_l = self._tournament_fight(w1, w2)
            m.append({"round":"胜者组决赛","a":w1.name,"b":w2.name,"winner":wf_w.name})
            # 败者组决赛
            lf_w, lf_l = self._tournament_fight(l1, l2)
            m.append({"round":"败者组决赛","a":l1.name,"b":l2.name,"winner":lf_w.name})
            # 决胜轮：胜者组决赛败方 vs 败者组决赛胜方 → 小组第二出线
            f_w, f_l = self._tournament_fight(wf_l, lf_w)
            m.append({"round":"决胜轮","a":wf_l.name,"b":lf_w.name,"winner":f_w.name})
            g["matches"] = m
            g["results"] = {"第一名": wf_w.name, "第二名": f_w.name}
            group_winners.append(wf_w)
            group_runners.append(f_w)

        # 8强：小组第一 vs 其他组第二（交叉配对）
        knockout = []
        quarter_pairs = []
        for i in range(len(group_names)):
            wi = i
            ri = (i + 1) % len(group_names)
            a = group_winners[wi] if wi < len(group_winners) else None
            b = group_runners[ri] if ri < len(group_runners) else None
            if a and b:
                quarter_pairs.append((a, b))

        if len(quarter_pairs) < 2:
            self._emit({"type": "tournament", "desc": "武道会8强人数不足，取消决赛"})
            self.tournament = {"groups": [{"name": g["name"], "players": [p.name for p in g["players"]], "matches": g["matches"], "results": g["results"]} for g in groups], "knockout": [], "champion": None}
            return

        current = []
        qf_matches = []
        for a, b in quarter_pairs:
            winner, loser = self._tournament_fight(a, b)
            qf_matches.append({"a": a.name, "b": b.name, "winner": winner.name})
            current.append(winner)
        knockout.append({"round": "8强", "matches": qf_matches})

        # 半决赛
        semi_pairs = []
        for i in range(0, len(current), 2):
            if i + 1 < len(current):
                semi_pairs.append((current[i], current[i + 1]))
        current2 = []
        sf_matches = []
        for a, b in semi_pairs:
            winner, loser = self._tournament_fight(a, b)
            sf_matches.append({"a": a.name, "b": b.name, "winner": winner.name})
            current2.append(winner)
        if sf_matches:
            knockout.append({"round": "半决赛", "matches": sf_matches})

        # 决赛
        champion = None
        if len(current2) >= 2:
            a, b = current2[0], current2[1]
            winner, loser = self._tournament_fight(a, b)
            knockout.append({"round": "决赛", "matches": [{"a": a.name, "b": b.name, "winner": winner.name}]})
            champion = winner
        elif len(current2) == 1:
            champion = current2[0]

        self.tournament = {
            "active": True,
            "groups": [{"name": g["name"], "players": [p.name for p in g["players"]], "matches": g["matches"], "results": g["results"]} for g in groups],
            "knockout": knockout,
            "champion": champion.name if champion else None,
        }

        if champion:
            champion.title = "天下第一人"
            champion.bonus_w += 10
            for c in self.alive():
                if c.id != champion.id:
                    self.rel[c.id][champion.id] = max(-100, self.rel[c.id].get(champion.id, 0) - 10)
                    self.rel[champion.id][c.id] = max(-100, self.rel[champion.id].get(c.id, 0) - 10)
            self._emit({"type": "tournament", "desc": f"天下第一武道会决赛！{champion.name}获得「天下第一人」称号！武力+10，众人对其好感-10"})


world = World()
