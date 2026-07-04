# app/ai/memory.py

class Memory:

    def __init__(self):
        self.store = {}

    def remember(self, npc, event):
        self.store.setdefault(npc.name, []).append(event)

    def build(self, npc, world_state):

        mem = self.store.get(npc.name, [])[-5:]

        return f"""
你是武侠NPC:{npc.name}
记忆:{mem}
世界:{world_state}

输出JSON:
{{
 "action":"war/ally/marry/assassinate/wait",
 "target":"name",
 "reason":"..."
}}
"""
