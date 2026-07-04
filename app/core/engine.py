from app.core.event_bus import EventBus
from app.ai.agent import Agent
from app.ai.llm import LLM
from app.ai.memory import Memory

class Engine:

    def __init__(self, world):

        self.world = world
        self.bus = EventBus()
        self.round = 0

        self.llm = LLM()
        self.memory = Memory()

        self.agents = [
            Agent(c, self.llm, self.memory)
            for c in world.characters.values()
        ]

    def tick(self):

        self.round += 1

        for a in self.agents:
            if not a.npc.alive:
                continue
            decision = a.decide(self.world)
            self.execute(a.npc, decision)

        self.resolve()

        self.bus.emit({
            "type": "round",
            "round": self.round,
            "desc": f"第{self.round}回合结束"
        })

        self.world.zhudi_move()
        self.world.check_movement()
        self.world.generate_tasks()
        self.world.combat_event()
        self.world.cooperation_event()
        self.world.do_tick_events()
        self.world.check_decay()
        self.world.maybe_start_tournament()
        self.world.huashan_battle()
        self.world._check_titles()

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
