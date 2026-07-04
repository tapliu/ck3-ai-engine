# app/core/world.py
from collections import defaultdict
from models.character import Character
import random

DATA = [
("ç”?,"é»„å®‡ç¿?,95,100,93,87),
("å¥?,"å•é’°è?,96,98,82,84),
("å¥?,"æ—ç»®æ€?,94,71,95,100),
("å¥?,"å¼ æ¢¦å¿?,89,79,100,92),
("ç”?,"æœ±æ££",100,87,91,97),
("ç”?,"å¼ ååº?,97,100,92,86)
]

class World:
    def __init__(self):
        self.characters = {}
        self.rel = defaultdict(dict)
        self.next_id = 0

        for d in DATA:
            self.create(*d)

    def create(self, gender, name, l, w, i, p):
        c = Character(self.next_id, name, gender, l, w, i, p)
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
            "characters":[c.to_dict() for c in self.alive()]
        }
