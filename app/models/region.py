import random


REGION_NAMES = ["中原", "江南", "塞北", "西域", "东海"]


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
