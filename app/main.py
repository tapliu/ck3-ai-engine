from fastapi import FastAPI
from app.core.world import World
from app.core.engine import Engine
from app.core.event_bus import EventBus

app = FastAPI()

world = World()
engine = Engine(world)

@app.get("/world")
def get_world():
    return world.export()

@app.post("/tick")
def tick():
    engine.tick()
    return {"ok":True}

@app.get("/events")
def events():
    return engine.bus.pop()
