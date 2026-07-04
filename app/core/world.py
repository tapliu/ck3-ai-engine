import os
import random
from collections import defaultdict
from app.models.character import Character


def _load_json(name):
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", name)
    if not os.path.isfile(path):
        return []
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


DATA = _load_json("chars.json")
TREASURES = _load_json("treasures.json")

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

        for d in DATA:
            self.create(d["gender"], d["name"], d["l"], d["w"], d["i"], d["p"], d.get("desc", ""), d.get("age", 20))

    def create(self, gender, name, l, w, i, p, desc="", age=20):
        c = Character(self.next_id, name, gender, l, w, i, p, desc, age)
        self.characters[self.next_id] = c

        for k in self.characters:
            if k != self.next_id:
                v = random.randint(-30, 30)
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
        pool = [c for c in self.alive_except_player() if c.age > self.player_char.age and not c.master]
        random.shuffle(pool)
        return pool[:3]

    def marry_candidates(self):
        if not self.player_char or self.triggers["marry"]:
            return []
        pool = [c for c in self.alive_except_player() if c.gender != self.player_char.gender and not c.spouse]
        random.shuffle(pool)
        return pool[:3]

    def sworn_candidates(self):
        if not self.player_char or self.triggers["sworn"]:
            return []
        pool = [c for c in self.alive_except_player()]
        random.shuffle(pool)
        return pool[:3]

    def export(self):
        return {
            "round": getattr(self, "engine", None) and self.engine.round or 0,
            "player": self.player_char.to_dict() if self.player_char else None,
            "triggers": self.triggers,
            "characters": [c.to_dict() for c in self.alive()]
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

    def random_treasure_event(self):
        if not TREASURES or not self.player_char:
            return
        available = [t for t in TREASURES if t["id"] not in self.used_treasures]
        if not available:
            return
        t = random.choice(available)
        self.used_treasures.add(t["id"])
        self.player_char.bonus_l += t.get("l", 0)
        self.player_char.bonus_w += t.get("w", 0)
        self.player_char.bonus_i += t.get("i", 0)
        self.player_char.bonus_p += t.get("p", 0)
        self.player_char.treasures.append(t["name"])
        tag = t["type"]
        self._emit({"type": "treasure", "desc": f"{self.player_char.name}奇遇获得【{t['name']}】（{tag}）：{t['desc']}"})

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
        c.bonus_l += t.get("l", 0)
        c.bonus_w += t.get("w", 0)
        c.bonus_i += t.get("i", 0)
        c.bonus_p += t.get("p", 0)
        c.treasures.append(t["name"])
        self._emit({"type": "treasure", "desc": f"{c.name}在江湖游历中获得【{t['name']}】"})

    def do_tick_events(self):
        self.random_wuxia_event()
        if random.random() < 0.3 and self.player_char:
            self.random_treasure_event()
        if random.random() < 0.2:
            self.character_treasure_event()


world = World()
