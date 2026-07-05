import os
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
