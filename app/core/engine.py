# app/core/engine.py

from app.core.event_bus import EventBus
from app.ai.agent import Agent
from app.ai.llm import LLM
from app.ai.memory import Memory

class Engine:

    def __init__(self, world):

        self.world = world
        self.bus = EventBus()

        self.llm = LLM()
        self.memory = Memory()

        self.agents = [
            Agent(c, self.llm, self.memory)
            for c in world.characters.values()
        ]

    def tick(self):

        # 1 AI决策
        for a in self.agents:

            if not a.npc.alive:
                continue

            decision = a.decide(self.world)

            self.execute(a.npc, decision)

        # 2 事件结算
        self.resolve()

    def execute(self, npc, d):

        if not d:
            return

        if d["action"] == "assassinate":
            t = self.world.get(d["target"])
            if t:
                t.alive = False
                self.bus.emit({
                    "type":"assassination",
                    "desc":f"{npc.name}刺杀{t.name}"
                })

        if d["action"] == "war":
            t = self.world.get(d["target"])
            if t:
                if npc.score() > t.score():
                    t.alive = False
                    self.bus.emit({
                        "type":"war",
                        "desc":f"{npc.name}击败{t.name}"
                    })

        self.memory.remember(npc, d)

    def resolve(self):
        pass
