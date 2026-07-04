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

# 外部区域中心城市（区域中心可进入中原）
REGIONAL_CENTERS = {
    "东海": "登州",
    "江南": "苏州",
    "西域": "敦煌",
    "塞北": "凉州",
}

# 区域中心到中原的连接
REGIONAL_CENTER_GATES = {
    "登州": "应天府",  # 东海→中原
    "苏州": "襄阳",    # 江南→中原
    "敦煌": "长安",    # 西域→中原
    "凉州": "燕京",    # 塞北→中原
}

# 外部区域间连接（东-南，南-西，西-北，北-东）
# 每个外部区域的三座城市全部参与对外连接
OUTER_CONNECTIONS = {
    "泉州": "苏州",    # 东海↔江南（东-南）
    "宁波": "扬州",    # 东海↔江南（东-南）
    "杭州": "于阗",    # 江南↔西域（南-西）
    "龟兹": "朔方",    # 西域↔塞北（西-北）
    "云中": "泉州",    # 塞北↔东海（北-东）→ 泉州成为连接江南和塞北的枢纽
}

# 合并所有连接（双向）
def _build_connections():
    conn = {}
    for a, b in REGIONAL_CENTER_GATES.items():
        conn.setdefault(a, []).append(b)
        conn.setdefault(b, []).append(a)
    for a, b in OUTER_CONNECTIONS.items():
        conn.setdefault(a, []).append(b)
        conn.setdefault(b, []).append(a)
    return conn

CITY_CONNECTIONS = _build_connections()


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


def get_city_info():
    """返回所有城市的详细信息"""
    info = {}
    for region, cities in CITIES.items():
        for city in cities:
            entry = {
                "region": region,
                "capital": city == CAPITAL,
                "regional_center": city in REGIONAL_CENTERS.values(),
                "connections": CITY_CONNECTIONS.get(city, []),
            }
            info[city] = entry
    return info
