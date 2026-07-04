from fastapi import APIRouter
from app.core.world import world

router = APIRouter(prefix="/api/world", tags=["world"])


@router.get("")
def get_world():
    return world.export()


@router.get("/characters")
def get_characters():
    return [c.to_dict() for c in world.alive()]
