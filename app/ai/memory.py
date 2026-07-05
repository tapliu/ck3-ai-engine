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
你的兵力:{npc.troops} 士气:{npc.morale} 训练度:{npc.training}
控制城池:{npc.controlled_cities}
个人武力:{npc.w} 智谋:{npc.p}
记忆:{mem}
世界:{world_state}

决策规则:
1. 兵力充足(>对方1.5倍)且关系<-20时选择"war"——系统会自动推演兵力、地形、战术
2. 关系<-40时选择"assassinate"——成功率与自身智谋和对方兵力有关
3. 关系>50时选择"ally"结盟或"marry"联姻
4. 优先攻打与你控制城池相邻的敌方城池以扩张势力
5. 兵力不足时选择"wait"积蓄力量

输出JSON:
{{
 "action":"war/assassinate/ally/marry/wait",
 "target":"name",
 "reason":"决策原因"
}}
"""
