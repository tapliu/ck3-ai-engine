---
name: game-ai
description: AI strategy rules for wuxia game simulation engine
---

# Wuxia Game AI Engine — Development Guide

## Project
A browser-based wuxia (martial arts) simulation game. Backend: Python FastAPI. Frontend: vanilla HTML/CSS/JS. AI agents use LLM (OpenAI) to decide NPC actions alongside procedural game systems.

## Architecture

### Core Loop (`engine.py`, `tick()`)
```
Agent LLM decisions → resolve → round event → movement → task gen → NPC auto-tasks → combat → cooperation → wuxia events → decay → age → tournament → titles
```

### Key files
| File | Role |
|---|---|
| `app/core/world.py` | Game state, task gen, movement, combat, tournaments, NPC auto-tasks |
| `app/core/engine.py` | Game loop orchestration |
| `app/core/event_bus.py` | In-memory event queue (emit/pop) |
| `app/models/character.py` | Character model (stats, cooldowns, relationships) |
| `app/models/region.py` | City graph, connections |
| `app/ai/agent.py` | Agent.decide() → memory build → LLM call |
| `app/ai/llm.py` | OpenAI wrapper |
| `app/ai/memory.py` | Prompt builder (last 5 decisions) |
| `app/main.py` | FastAPI routes + static files |
| `frontend/index.html` | All UI (inline CSS + JS) |

## Conventions

### Backend
- **Modify in place**: world.py mutates `self` state directly; no return values
- **Events**: Call `self._emit({"type": str, "desc": str})` to broadcast events — `_emit` auto-attaches `round`
- **NPC iteration**: Use `self.alive_except_player()` or `self.alive()` — never iterate `self.characters` directly
- **Task format**: `{"name", "desc", "diff": int, "stat": "l"/"w"/"i"/"p", "tag": "non_char"/"char"/"deadly"/"coop"}`
- **Character lookup**: `self.get(name)` searches `self.characters.values()` by `.name`
- **Stat fields**: `base_l/w/i/p` + computed property `l/w/i/p` = `base + bonus`; use `.w` for total stat
- **Cooldowns**: `next_move_round`, `scheme_cooldown_round`, `focus_cooldown_round`, `rush_cooldown_round` — compare against `self.engine.round`
- **Collections**: `from collections import defaultdict` for grouping (cities, regions, etc.)

### Frontend
- **Overlays**: One modal at a time — controlled by `classList.add/remove('active')`
- **Priority chain**: move → event → decay → task (in `tick()` + `doAutoTick()`)
- **Auto-tick**: `doAutoTick()` handles overlays sequentially, does ONE `tick()` per session
- **Event rendering**: `TYPE_CLASS` map in `fetchEvents()` — add new types there
- **CSS**: Classes `event-{type}` for event colors; `.overlay` modals with `flex centering`

### API
- `POST /tick` calls `engine.tick()` — no request body, response `{"ok": true}`
- `GET /api/tournament` returns `world.tournament` or fallback `{"active": false, ...}`
- `GET /api/events` pops and returns all events from bus
- `GET /api/world` returns `world.export()` — full state snapshot

## Game AI Rules

- **Eval stat first**: Compare `npc.w` (total martial) when deciding war — only attack if `(npc.w - target.w) > random(5, 20)`
- **Cooldown aware**: Don't target scheme/focus actions if cooldown active; fall back to normal mode
- **Relationship threshold**: War below -20; assassinate below -40; ally/marry above +50
- **Territory**: Prefer same-region targets; moving to enemy region costs 2+ turns
- **Resource**: Treasure bonuses matter — target characters with high-value treasures
- **Task selection**: Pick highest probability mode among normal/scheme/focus; choose tasks where stat > difficulty by at least 10 points
- **Coop priority**: Cooperate with same-city characters over same-region; coop gives bonus rewards
- **Deadly task**: Only attempt when stat > difficulty by 15+ (death risk otherwise)
- **Defense first**: When outnumbered 3:1 in region, move away rather than fight
- **No unnecessary war**: War reduces relationship globally; prefer assassination for high-value targets
- **Chivalry**: High xia_yi characters get tournament priority; balance stat gains with chivalry

## Data Model (Character)

```
id, name, gender, alive, age, region, city, dynasty, desc
l/w/i/p (computed: base_* + bonus_*)
base_l, base_w, base_i, base_p (initial, fixed)
bonus_l, bonus_w, bonus_i, bonus_p (from tasks/treasures)
xia_yi, title, titles[], treasures[]
spouse, master, sworn_brothers[] (life events)
next_move_round, scheme_cooldown_round, focus_cooldown_round, rush_cooldown_round
score() = l*0.25 + w*0.35 + i*0.2 + p*0.2
```

## Region Topology

5 regions, 18 cities, CITY_CONNECTIONS adjacency dict.
- 中原: 6 cities (capital: 应天府), interior cycle
- 江南/塞北/西域/东海: 3 cities each, fully connected internally
- Regional centers connect to specific 中原 cities (gateways)
- Cross-region edges connect non-中原 cities (e.g., 泉州↔扬州)

## Task System

- `generate_tasks()`: 1-3 per round from NON_CHAR + CHAR pool; 30% include DEADLY; auto-convert to COOP if NPCs nearby
- `npc_task()`: 50% chance per NPC per round; picks best mode automatically; cooldowns enforced
- Success formula: `min(95, max(5, 50 + (stat - diff) * 0.5))` for normal; `* 0.75` for focus
- `execute_task()`: Player picks mode; clears `pending_tasks` after any execution; deadly failure can kill player
- Task types: non_char (l/w focus), char (i focus), deadly (high diff, death risk), coop (with partner)

## New Feature Template

1. Add data model fields to `Character` (if needed) — init defaults in `__init__`
2. Add state fields to `World.__init__` (if needed)
3. Implement logic in `world.py` method — use `_emit()` for events
4. Call the method from `engine.py` `tick()` at appropriate position
5. Add API route in `main.py` (GET/POST)
6. Add frontend handler + CSS + overlay in `index.html`
7. Add event type to `TYPE_CLASS` map if new event type
