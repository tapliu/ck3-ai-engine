from fastapi import APIRouter
from app.core.world import world

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("")
def get_events():
    return world.engine.bus.pop() if hasattr(world, "engine") else []
