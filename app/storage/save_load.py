import json
import os
from app.config import settings


def save_world(world, name: str = "savegame"):
    path = os.path.join(settings.save_dir, f"{name}.json")
    os.makedirs(settings.save_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(world.export(), f, ensure_ascii=False, indent=2)
    return path


def load_world(world, name: str = "savegame"):
    path = os.path.join(settings.save_dir, f"{name}.json")
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in world.characters.values():
        match = next(
            (d for d in data.get("characters", []) if d["name"] == c.name), None
        )
        if match:
            c.alive = match.get("alive", True)
    return True
