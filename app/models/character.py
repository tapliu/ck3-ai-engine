import random

REGIONS = ["中原","江南","塞北","西域","东海"]

class Character:
    def __init__(self, cid, name, gender, l, w, i, p, desc="", age=20):
        self.id = cid
        self.name = name
        self.gender = gender
        self.l = l
        self.w = w
        self.i = i
        self.p = p
        self.age = age

        self.alive = True
        self.region = random.choice(REGIONS)
        self.dynasty = name
        self.desc = desc

        self.spouse = None
        self.master = None
        self.sworn_brothers = []
        self.treasures = []

        self.memory = []

    def score(self):
        return self.l*0.25 + self.w*0.35 + self.i*0.2 + self.p*0.2

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "region": self.region,
            "dynasty": self.dynasty,
            "desc": self.desc,
            "l": self.l,
            "w": self.w,
            "i": self.i,
            "p": self.p,
            "score": round(self.score(), 2),
            "alive": self.alive,
            "spouse": self.spouse,
            "master": self.master,
            "sworn_brothers": self.sworn_brothers,
            "treasures": self.treasures,
            "memory": self.memory[-5:],
        }
