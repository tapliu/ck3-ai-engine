import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.core.world import world
from app.core.engine import Engine
from app.api.world_api import router as world_router
from app.api.npc_api import router as npc_router
from app.api.event_api import router as event_router

app = FastAPI(title="CK3 AI Engine")

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
