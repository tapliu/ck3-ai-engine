import os
import random
from collections import defaultdict
from app.models.character import Character


def _load_data():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chars.json")
    if not os.path.isfile(path):
        return []

    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


DATA = _load_data()


class World:
    def __init__(self):
        self.characters = {}
        self.rel = defaultdict(dict)
        self.next_id = 0

        for d in DATA:
            self.create(d["gender"], d["name"], d["l"], d["w"], d["i"], d["p"], d.get("desc", ""))

    def create(self, gender, name, l, w, i, p, desc=""):
        c = Character(self.next_id, name, gender, l, w, i, p, desc)
        self.characters[self.next_id] = c

        for k in self.characters:
            if k != self.next_id:
                v = random.randint(-30, 30)
                self.rel[k][self.next_id] = v
                self.rel[self.next_id][k] = v

        self.next_id += 1

    def alive(self):
        return [c for c in self.characters.values() if c.alive]

    def get(self, name):
        for c in self.characters.values():
            if c.name == name:
                return c

    def export(self):
        return {
            "round": getattr(self, "engine", None) and self.engine.round or 0,
            "characters":[c.to_dict() for c in self.alive()]
        }


world = World()
