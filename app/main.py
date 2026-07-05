import os
import pickle
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.core.world import world
from app.core.engine import Engine
from app.api.world_api import router as world_router
from app.api.npc_api import router as npc_router
from app.api.event_api import router as event_router

app = FastAPI(title="浪子江湖-侠行四海")

engine = Engine(world)
world.engine = engine

SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "save.dat")

app.include_router(world_router)
app.include_router(npc_router)
app.include_router(event_router)

images_path = os.path.join(os.path.dirname(__file__), "..", "data", "Images")
if os.path.isdir(images_path):
    app.mount("/api/images", StaticFiles(directory=images_path), name="images")

data_path = os.path.join(os.path.dirname(__file__), "..", "data")
if os.path.isdir(data_path):
    app.mount("/api/data", StaticFiles(directory=data_path), name="data")


@app.get("/")
def index():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.isfile(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return {"error": "frontend not found"}


@app.post("/tick")
def tick():
    engine.tick()
    return {"ok": True}


@app.get("/api/start/candidates")
def start_candidates():
    cs = world.start_candidates()
    return [c.to_dict() for c in cs]


class SelectPlayer(BaseModel):
    name: str


@app.post("/api/new_game")
def new_game():
    world.new_game()
    engine.reset()
    return {"ok": True}

@app.post("/api/save")
def save_game():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, 'wb') as f:
        pickle.dump((world, engine), f)
    return {"ok": True}

@app.post("/api/load")
def load_game():
    if not os.path.isfile(SAVE_PATH):
        return {"ok": False, "error": "no_save"}
    with open(SAVE_PATH, 'rb') as f:
        saved_world, saved_engine = pickle.load(f)
    world.__dict__.clear()
    world.__dict__.update(saved_world.__dict__)
    engine.__dict__.clear()
    engine.__dict__.update(saved_engine.__dict__)
    world.engine = engine
    engine.world = world
    return {"ok": True}

@app.post("/api/start/select")
def select_player(body: SelectPlayer):
    c = world.set_player(body.name)
    return {"ok": True, "player": c.to_dict()}


@app.get("/api/events/pending")
def pending_events():
    if not world.player_char:
        return {"events": []}
    result = []
    for etype, label in [("apprentice", "拜师"), ("marry", "结婚"), ("sworn", "结拜")]:
        if world.triggers.get(etype):
            continue
        candidates = getattr(world, f"{etype}_candidates")()
        if candidates:
            result.append({"event": etype, "label": label, "candidates": [c.to_dict() for c in candidates]})
    # only return the first pending event
    if result:
        return {"events": result[:1]}
    return {"events": []}


class DecideEvent(BaseModel):
    event: str
    target: str


@app.post("/api/events/decide")
def decide_event(body: DecideEvent):
    method = getattr(world, f"do_{body.event}", None)
    if method:
        method(body.target)
    return {"ok": True}


@app.get("/api/tasks/pending")
def pending_tasks():
    return {"tasks": world.pending_task_data()}


class ExecuteTask(BaseModel):
    task_id: int
    use_scheme: bool = False
    mode: str = "normal"


@app.post("/api/tasks/execute")
def execute_task(body: ExecuteTask):
    m = body.mode if body.mode != "normal" else ("scheme" if body.use_scheme else "normal")
    return world.execute_task(body.task_id, m)


# ---- 不进则退 ----

@app.get("/api/decay/pending")
def decay_pending():
    if world.pending_decay:
        return world.pending_decay
    return {"decay": None}


class DecayChoice(BaseModel):
    field: str


@app.post("/api/decay/execute")
def execute_decay(body: DecayChoice):
    return world.execute_decay(body.field)


# ---- 移动系统 ----

class MoveRequest(BaseModel):
    dest: str = ""
    action: str = "move"  # "move", "stay", "rush"


@app.get("/api/move/pending")
def get_movement():
    return world.pending_move or {"city": None, "routes": []}

@app.post("/api/move")
def execute_move(body: MoveRequest):
    result = world.execute_move(dest=body.dest, action=body.action)
    if not result.get("ok"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(result))
    return result

# ---- 天下第一武道会 ----

@app.get("/api/tournament")
def get_tournament():
    return world.tournament or {"active": False, "groups": [], "knockout": [], "champion": None}

# ---- 武将编辑 ----

CHARS_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "chars.json")

@app.get("/api/characters/edit")
def get_characters_edit():
    import json
    with open(CHARS_JSON, "r", encoding="utf-8") as f:
        original = json.load(f)
    current = []
    for c in world.characters.values():
        current.append({
            "id": c.id, "name": c.name, "gender": c.gender,
            "l": c.base_l, "w": c.base_w, "i": c.base_i, "p": c.base_p,
            "age": c.age, "desc": c.desc,
        })
    return {"original": original, "current": current}

class CharEditItem(BaseModel):
    id: int
    name: str
    gender: str
    l: int
    w: int
    i: int
    p: int
    age: int
    desc: str

@app.post("/api/characters/save")
def save_characters(items: list[CharEditItem]):
    import json
    # Update in-memory characters
    for item in items:
        c = world.characters.get(item.id)
        if c:
            c.base_l = item.l
            c.base_w = item.w
            c.base_i = item.i
            c.base_p = item.p
            c.age = item.age
            c.desc = item.desc
            c.name = item.name
            c.gender = item.gender
    # Update chars.json
    data = [{"gender": it.gender, "name": it.name, "l": it.l, "w": it.w, "i": it.i, "p": it.p, "desc": it.desc, "age": it.age} for it in items]
    with open(CHARS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Update module-level DATA
    from app.core.world import DATA
    DATA.clear()
    DATA.extend(data)
    return {"ok": True}

@app.post("/api/characters/reset")
def reset_characters():
    import json
    with open(CHARS_JSON, "r", encoding="utf-8") as f:
        original = json.load(f)
    name_to_char = {c.name: c for c in world.characters.values()}
    for d in original:
        c = name_to_char.get(d["name"])
        if c:
            c.base_l = d["l"]
            c.base_w = d["w"]
            c.base_i = d["i"]
            c.base_p = d["p"]
            c.age = d.get("age", 20)
            c.desc = d.get("desc", "")
            c.gender = d["gender"]
            c.bonus_l = 0
            c.bonus_w = 0
            c.bonus_i = 0
            c.bonus_p = 0
    from app.core.world import DATA
    DATA.clear()
    DATA.extend(original)
    return {"ok": True}

# ---- 自建武将 ----

CUSTOM_CHARS_JSON = os.path.join(os.path.dirname(__file__), "..", "data", "custom_chars.json")

def _read_custom_chars():
    import json
    if not os.path.isfile(CUSTOM_CHARS_JSON):
        return []
    with open(CUSTOM_CHARS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_custom_chars(data):
    import json
    os.makedirs(os.path.dirname(CUSTOM_CHARS_JSON), exist_ok=True)
    with open(CUSTOM_CHARS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/api/characters/custom")
def list_custom_chars():
    return {"chars": _read_custom_chars()}

class CustomCharCreate(BaseModel):
    name: str
    gender: str
    l: int
    w: int
    i: int
    p: int
    age: int
    desc: str = ""
    imageIdx: int = 1

@app.post("/api/characters/custom/create")
def create_custom_char(body: CustomCharCreate):
    chars = _read_custom_chars()
    new_id = max([c["id"] for c in chars], default=-1) + 1
    entry = {
        "id": new_id,
        "name": body.name,
        "gender": body.gender,
        "l": body.l,
        "w": body.w,
        "i": body.i,
        "p": body.p,
        "age": body.age,
        "desc": body.desc,
        "imageIdx": body.imageIdx,
    }
    chars.append(entry)
    _write_custom_chars(chars)
    # Also add to current world if a game is active
    if world.characters and world.characters:
        world.create(body.gender, body.name, body.l, body.w, body.i, body.p, body.desc, body.age, body.imageIdx, new_id)
    return {"ok": True, "char": entry}

class CustomCharUpdate(BaseModel):
    id: int
    name: str
    gender: str
    l: int
    w: int
    i: int
    p: int
    age: int
    desc: str = ""
    imageIdx: int = 1

@app.post("/api/characters/custom/update")
def update_custom_char(body: CustomCharUpdate):
    chars = _read_custom_chars()
    found = None
    for c in chars:
        if c["id"] == body.id:
            c.update({
                "name": body.name,
                "gender": body.gender,
                "l": body.l,
                "w": body.w,
                "i": body.i,
                "p": body.p,
                "age": body.age,
                "desc": body.desc,
                "imageIdx": body.imageIdx,
            })
            found = c
            break
    if not found:
        return {"ok": False, "error": "not_found"}
    _write_custom_chars(chars)
    # Update in current world
    for c in world.characters.values():
        if c.custom_id == body.id:
            c.name = body.name
            c.gender = body.gender
            c.base_l = body.l
            c.base_w = body.w
            c.base_i = body.i
            c.base_p = body.p
            c.age = body.age
            c.desc = body.desc
            c.imageIdx = body.imageIdx
            break
    return {"ok": True, "char": found}

class CustomCharDelete(BaseModel):
    id: int

@app.post("/api/characters/custom/delete")
def delete_custom_char(body: CustomCharDelete):
    chars = _read_custom_chars()
    chars = [c for c in chars if c["id"] != body.id]
    _write_custom_chars(chars)
    # Remove from current world
    to_remove = [cid for cid, c in world.characters.items() if c.custom_id == body.id]
    for cid in to_remove:
        del world.characters[cid]
    return {"ok": True}
