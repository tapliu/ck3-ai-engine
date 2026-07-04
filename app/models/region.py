import random


REGION_NAMES = ["中原", "江南", "塞北", "西域", "东海"]

CITIES = {
    "中原": ["洛阳", "开封", "长安", "许昌", "邺城", "襄阳"],
    "江南": ["苏州", "杭州", "扬州"],
    "塞北": ["凉州", "朔方", "云中"],
    "西域": ["敦煌", "龟兹", "于阗"],
    "东海": ["泉州", "宁波", "登州"],
}

ALL_CITIES = [c for clist in CITIES.values() for c in clist]


class Region:
    def __init__(self, name: str):
        self.name = name
        self.controlled_by: int | None = None

    def to_dict(self):
        return {
            "name": self.name,
            "controlled_by": self.controlled_by,
        }


def random_region() -> str:
    return random.choice(REGION_NAMES)


def random_city(region: str = None) -> str:
    if region:
        return random.choice(CITIES.get(region, ALL_CITIES))
    return random.choice(ALL_CITIES)
