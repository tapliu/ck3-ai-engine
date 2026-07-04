from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
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

try:
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
except RuntimeError:
    pass


@app.get("/")
def index():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app/")


@app.post("/tick")
def tick():
    engine.tick()
    return {"ok": True}



