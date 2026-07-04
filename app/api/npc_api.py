from fastapi import APIRouter, HTTPException
from app.core.world import world

router = APIRouter(prefix="/api/npc", tags=["npc"])


@router.get("/{name}")
def get_npc(name: str):
    c = world.get(name)
    if not c:
        raise HTTPException(404, "NPC not found")
    return c.to_dict()


@router.get("/{name}/memory")
def get_npc_memory(name: str):
    c = world.get(name)
    if not c:
        raise HTTPException(404, "NPC not found")
    return {"name": name, "memory": c.memory}
