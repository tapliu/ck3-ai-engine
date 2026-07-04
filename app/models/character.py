# app/models/character.py
import random

REGIONS = ["中原","江南","塞北","西域","东海"]

class Character:
    def __init__(self, cid, name, gender, l, w, i, p):
        self.id = cid
        self.name = name
        self.gender = gender

        self.l = l
        self.w = w
        self.i = i
        self.p = p

        self.alive = True
        self.region = random.choice(REGIONS)

        self.dynasty = name
        self.spouse = None

        self.memory = []

    def score(self):
        return self.l*0.25 + self.w*0.35 + self.i*0.2 + self.p*0.2

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "region": self.region,
            "dynasty": self.dynasty,
            "spouse": self.spouse,
            "l": self.l,
            "w": self.w,
            "i": self.i,
            "p": self.p,
            "score": round(self.score(), 2),
            "alive": self.alive,
            "memory": self.memory[-5:],
        }
