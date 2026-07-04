# app/ai/agent.py

class Agent:

    def __init__(self, npc, llm, memory):
        self.npc = npc
        self.llm = llm
        self.memory = memory

    def decide(self, world):

        prompt = self.memory.build(self.npc, world.export())

        return self.llm.call(prompt)
