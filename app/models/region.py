import random

REGION_NAMES = ["中原", "江南", "塞北", "西域", "东海"]

CITIES = {
    "中原": ["洛阳", "开封", "长安", "燕京", "应天府", "襄阳"],
    "江南": ["苏州", "杭州", "扬州"],
    "塞北": ["凉州", "朔方", "云中"],
    "西域": ["敦煌", "龟兹", "于阗"],
    "东海": ["泉州", "宁波", "登州"],
}

ALL_CITIES = [c for clist in CITIES.values() for c in clist]

CAPITAL = "应天府"

REGIONAL_CENTERS = {
    "东海": "登州",
    "江南": "苏州",
    "西域": "敦煌",
    "塞北": "凉州",
}

REGIONAL_CENTER_GATES = {
    "登州": "应天府",
    "苏州": "襄阳",
    "敦煌": "长安",
    "凉州": "燕京",
}

OUTER_CONNECTIONS = {
    "泉州": "扬州",
    "宁波": "云中",
    "杭州": "于阗",
    "龟兹": "朔方",
}

INNER_RING = [
    ("长安", "燕京"),
    ("燕京", "应天府"),
    ("应天府", "襄阳"),
    ("襄阳", "长安"),
]

INNER_CITY_CONNECTIONS = {
    "洛阳": ["长安", "燕京", "开封"],
    "开封": ["应天府", "襄阳", "洛阳"],
}

MINOR_REGION_CONNECTIONS = {
    "江南": [("苏州", "杭州"), ("苏州", "扬州"), ("杭州", "扬州")],
    "塞北": [("凉州", "朔方"), ("凉州", "云中"), ("朔方", "云中")],
    "西域": [("敦煌", "龟兹"), ("敦煌", "于阗"), ("龟兹", "于阗")],
    "东海": [("泉州", "宁波"), ("泉州", "登州"), ("宁波", "登州")],
}

TERRAIN_TYPES = {
    "中原": {
        "洛阳": "平原", "开封": "平原", "长安": "山地", "燕京": "平原",
        "应天府": "水域", "襄阳": "山地",
    },
    "江南": {"苏州": "水域", "杭州": "水域", "扬州": "平原"},
    "塞北": {"凉州": "荒漠", "朔方": "荒漠", "云中": "山地"},
    "西域": {"敦煌": "荒漠", "龟兹": "荒漠", "于阗": "山地"},
    "东海": {"泉州": "水域", "宁波": "水域", "登州": "平原"},
}

TERRAIN_MODIFIERS = {
    "平原": {"attack": 1.0, "defense": 1.0, "move_cost": 1},
    "山地": {"attack": 0.8, "defense": 1.4, "move_cost": 2},
    "水域": {"attack": 0.7, "defense": 1.2, "move_cost": 2},
    "荒漠": {"attack": 0.9, "defense": 0.8, "move_cost": 2},
}

# 城池初始经济数据
CITY_ECONOMY_BASE = {
    "洛阳": {"dev": 70, "pop": 80000, "garrison": 2000},
    "开封": {"dev": 65, "pop": 75000, "garrison": 1800},
    "长安": {"dev": 75, "pop": 90000, "garrison": 2500},
    "燕京": {"dev": 55, "pop": 60000, "garrison": 1500},
    "应天府": {"dev": 80, "pop": 100000, "garrison": 3000},
    "襄阳": {"dev": 60, "pop": 65000, "garrison": 2000},
    "苏州": {"dev": 70, "pop": 70000, "garrison": 1500},
    "杭州": {"dev": 65, "pop": 65000, "garrison": 1200},
    "扬州": {"dev": 55, "pop": 55000, "garrison": 1000},
    "凉州": {"dev": 40, "pop": 35000, "garrison": 1500},
    "朔方": {"dev": 35, "pop": 30000, "garrison": 1200},
    "云中": {"dev": 30, "pop": 25000, "garrison": 1000},
    "敦煌": {"dev": 35, "pop": 30000, "garrison": 1000},
    "龟兹": {"dev": 30, "pop": 25000, "garrison": 800},
    "于阗": {"dev": 25, "pop": 20000, "garrison": 800},
    "泉州": {"dev": 45, "pop": 40000, "garrison": 1000},
    "宁波": {"dev": 40, "pop": 35000, "garrison": 800},
    "登州": {"dev": 40, "pop": 35000, "garrison": 1000},
}


def _build_connections():
    conn = {}
    for a, b in REGIONAL_CENTER_GATES.items():
        conn.setdefault(a, []).append(b)
        conn.setdefault(b, []).append(a)
    for a, b in OUTER_CONNECTIONS.items():
        conn.setdefault(a, []).append(b)
        conn.setdefault(b, []).append(a)
    for a, b in INNER_RING:
        conn.setdefault(a, []).append(b)
        conn.setdefault(b, []).append(a)
    for city, neighbors in INNER_CITY_CONNECTIONS.items():
        for n in neighbors:
            if n not in conn.get(city, []):
                conn.setdefault(city, []).append(n)
                conn.setdefault(n, []).append(city)
    for _region, pairs in MINOR_REGION_CONNECTIONS.items():
        for a, b in pairs:
            if b not in conn.get(a, []):
                conn.setdefault(a, []).append(b)
                conn.setdefault(b, []).append(a)
    return conn

CITY_CONNECTIONS = _build_connections()


class CityState:
    def __init__(self, name: str, region: str):
        self.name = name
        self.region = region
        base = CITY_ECONOMY_BASE.get(name, {"dev": 30, "pop": 20000, "garrison": 500})
        self.development = base["dev"]
        self.population = base["pop"]
        self.garrison = base["garrison"]
        self.controller = None
        self.terrain = TERRAIN_TYPES.get(region, {}).get(name, "平原")

    @property
    def terrain_mod(self):
        return TERRAIN_MODIFIERS.get(self.terrain, TERRAIN_MODIFIERS["平原"])

    def to_dict(self):
        return {
            "name": self.name,
            "region": self.region,
            "development": self.development,
            "population": self.population,
            "garrison": self.garrison,
            "controller": self.controller,
            "terrain": self.terrain,
        }


def get_city_info():
    info = {}
    for region, cities in CITIES.items():
        for city in cities:
            entry = {
                "region": region,
                "capital": city == CAPITAL,
                "regional_center": city in REGIONAL_CENTERS.values(),
                "connections": CITY_CONNECTIONS.get(city, []),
                "terrain": TERRAIN_TYPES.get(region, {}).get(city, "平原"),
            }
            info[city] = entry
    return info


def random_region() -> str:
    return random.choice(REGION_NAMES)


def random_city(region: str = None) -> str:
    if region:
        return random.choice(CITIES.get(region, ALL_CITIES))
    return random.choice(ALL_CITIES)
