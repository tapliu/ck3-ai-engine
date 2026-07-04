import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
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
