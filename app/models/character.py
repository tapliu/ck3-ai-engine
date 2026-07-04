import random

REGIONS = ["中原","江南","塞北","西域","东海"]

class Character:
    def __init__(self, cid, name, gender, l, w, i, p, desc="", age=20):
        self.id = cid
        self.name = name
        self.gender = gender
        self.base_l = l
        self.base_w = w
        self.base_i = i
        self.base_p = p
        self.bonus_l = 0
        self.bonus_w = 0
        self.bonus_i = 0
        self.bonus_p = 0
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

    @property
    def l(self):
        return self.base_l + self.bonus_l

    @property
    def w(self):
        return self.base_w + self.bonus_w

    @property
    def i(self):
        return self.base_i + self.bonus_i

    @property
    def p(self):
        return self.base_p + self.bonus_p

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
            "base_l": self.base_l,
            "base_w": self.base_w,
            "base_i": self.base_i,
            "base_p": self.base_p,
            "bonus_l": self.bonus_l,
            "bonus_w": self.bonus_w,
            "bonus_i": self.bonus_i,
            "bonus_p": self.bonus_p,
            "score": round(self.score(), 2),
            "alive": self.alive,
            "spouse": self.spouse,
            "master": self.master,
            "sworn_brothers": self.sworn_brothers,
            "treasures": self.treasures,
            "memory": self.memory[-5:],
        }
