import random
from app.core.event_bus import EventBus
from app.core.battle import sim_battle, pick_tactic
from app.core.economy import tick_economy, try_expand, conquer_city
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

        # 经济系统
        tick_economy(self.world)

        self.world.zhudi_move()
        self.world.check_movement()
        self.world.generate_tasks()
        # NPC 自动执行任务
        for c in self.world.alive_except_player():
            if random.random() < 0.5:
                self.world.npc_task(c)
        # 旧战斗（不和引起）
        self.world.combat_event()
        # 新战斗系统：AI势力扩张
        if self.round > 0 and self.round % 3 == 0:
            for c in self.world.alive_except_player():
                if c.troops < 100:
                    continue
                target = try_expand(self.world, c)
                if target:
                    city_state = self.world.city_states.get(target)
                    defender = None
                    if city_state and city_state.controller:
                        defender = self.world.characters.get(city_state.controller)
                    if defender and defender.alive:
                        result = sim_battle(c, defender, target, self.world)
                        if result["result"] == "attacker_win":
                            conquer_city(self.world, c, target, result)
                        self.bus.emit({"type": "battle", "desc": f"{c.name}攻打{target}！{'获胜' if result['result']=='attacker_win' else '失败'}", "battle_result": result})
                        for log in result["logs"][:3]:
                            self.bus.emit({"type": "battle_log", "desc": log, "battle_result": result})
                    else:
                        conquer_city(self.world, c, target, None)

        self.world.cooperation_event()
        self.world.do_tick_events()
        self.world.check_decay()
        self.world.age_all()
        self.world.maybe_start_tournament()
        self.world.huashan_battle()
        self.world._check_titles()

    def reset(self):
        self.bus = EventBus()
        self.round = 0
        self.memory = Memory()
        self.agents = [
            Agent(c, self.llm, self.memory)
            for c in self.world.characters.values()
        ]

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
