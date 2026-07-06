import random
from copy import deepcopy
from app.models.region import CITIES

REGIONS = ["中原","江南","塞北","西域","东海"]

SKILL_TEMPLATES = [
    {"type": "damage", "name": "烈焰斩", "desc": "凝聚火劲，造成大量伤害"},
    {"type": "damage", "name": "穿心箭", "desc": "一箭穿心，精准打击"},
    {"type": "damage", "name": "雷霆击", "desc": "引雷入体，雷霆万钧"},
    {"type": "damage", "name": "剑气纵横", "desc": "剑气纵横，所向披靡"},
    {"type": "silence", "name": "封喉诀", "desc": "封住对手经脉，2回合无法施技"},
    {"type": "silence", "name": "哑穴点", "desc": "点中哑穴，沉默对手"},
    {"type": "stun", "name": "定身术", "desc": "内力禁锢，1回合无法行动"},
    {"type": "stun", "name": "迷魂咒", "desc": "迷惑心智，令对手原地不动"},
]

def random_skill():
    skill = random.choice(SKILL_TEMPLATES)
    return {"type": skill["type"], "name": skill["name"], "desc": skill["desc"]}


class Character:
    def __init__(self, cid, name, gender, l, w, i, p, desc="", age=20, imageIdx=None, custom_id=None):
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
        self.imageIdx = imageIdx
        self.custom_id = custom_id

        self.alive = True
        self.region = random.choice(REGIONS)
        self.city = None
        self.dynasty = name
        self.next_move_round = 0
        self.scheme_cooldown_round = 0
        self.focus_cooldown_round = 0
        self.rush_cooldown_round = 0
        self.desc = desc

        self.spouse = None
        self.master = None
        self.sworn_brothers = []
        self.treasures = []
        self.xia_yi = 0
        self.title = ""
        self.titles = []

        self.memory = []

        # 军事
        self.troops = 500
        self.morale = 50
        self.training = 30
        self.controlled_cities = []
        self.gold = 200

        self.skill = random_skill()
        self.is_emperor = False

        self._init_l = self.l
        self._init_w = self.w
        self._init_i = self.i
        self._init_p = self.p

    def __setstate__(self, state):
        self.__dict__.update(state)
        if 'gold' not in self.__dict__:
            self.gold = 200
        if 'skill' not in self.__dict__:
            self.skill = random_skill()
        if 'is_emperor' not in self.__dict__:
            self.is_emperor = False

    def init_stats(self):
        self._init_l = self.l
        self._init_w = self.w
        self._init_i = self.i
        self._init_p = self.p

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

    def main_title(self):
        max_stat = max(self.l, self.w, self.p)
        if self.l == max_stat:
            return "鬼谷子"
        elif self.w == max_stat:
            return "万人敌"
        else:
            return "智多星"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "age": self.age,
            "main_title": self.main_title(),
            "region": self.region,
            "city": self.city,
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
            "xia_yi": self.xia_yi,
            "title": self.title,
            "titles": self.titles,
            "next_move_round": self.next_move_round,
            "scheme_cooldown_round": self.scheme_cooldown_round,
            "focus_cooldown_round": self.focus_cooldown_round,
            "rush_cooldown_round": self.rush_cooldown_round,
            "troops": self.troops,
            "morale": self.morale,
            "training": self.training,
            "controlled_cities": self.controlled_cities,
            "memory": self.memory[-5:],
            "init_l": self._init_l,
            "init_w": self._init_w,
            "init_i": self._init_i,
            "init_p": self._init_p,
            "imageIdx": self.imageIdx,
            "skill": getattr(self, 'skill', random_skill()),
            "gold": getattr(self, 'gold', 200),
            "is_emperor": getattr(self, 'is_emperor', False),
        }
