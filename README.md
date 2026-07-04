# 浪子江湖 · 侠行四海

AI 驱动的武侠江湖模拟游戏。35 位角色出自小说《浪子江湖》，每人有机敏、武力、魅力、智谋四项属性及年龄、描述。

## 快速开始

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

浏览器打开 `http://localhost:8000`

## 游戏玩法

1. **选人** — 开局从 3 个随机角色中选择你的侠客
2. **Tick** — 每点击一次推进一回合，NPC 会自主决策（战争、刺杀等）
3. **任务** — 每回合出现 1–2 个江湖任务，分非人物类/人物类/合作三类，可选择三种执行模式：
   - **普通** — 使用任务主属性计算成功率
   - **用谋略** — 普通 + 智谋 × 0.1 加成
   - **全力施展** — 属性贡献 × 1.5，成功率最高
4. **事件** — 好感度 ≥ 60 且满足条件角色 ≥ 3 人时触发拜师、结婚、结拜等人生大事
5. **奇遇** — 玩家 30%/NPC 20% 概率获得宝物，属性随之成长
6. **侠义值** — 完成任务成功增加 2–5 侠义值，影响武道会参赛资格
7. **不进则退**（每 10 回合）— 选择一项属性降低 10%
8. **天下第一武道会**（每 30 回合）— 侠义值 Top 16 参赛，小组循环赛 → 8 强淘汰赛 → 冠军获「天下第一人」称号，武力 +10，众人好感 -10
9. **NPC 排序** — 可按默认/好感/机敏/武力/魅力/智谋/侠义值排序展示

## 属性系统

- **机敏(l)** — 非人物类任务成功率
- **武力(w)** — 战斗力，武道会决胜关键
- **魅力(i)** — 人物类任务成功率
- **智谋(p)** — 谋略任务加成（系数 × 0.1）
- **侠义值** — 通过任务积累，影响武道会资格
- 属性按 `总值(基础值+加成值)` 分开展示（如 107 = 95 + 12）

## 好感度系统

- 初始好感随机范围 -20~20
- 合作任务成功 +10~20，失败 -5~10
- 拜师/结婚/结拜需好感 ≥ 60
- 同区域关係 < -5 可能爆发战斗，> 5 可能和睦互助

## 项目结构

```
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── core/
│   │   ├── world.py         # 世界状态 + 事件 + 任务 + 武道会
│   │   ├── engine.py        # 游戏主循环
│   │   └── event_bus.py     # 事件总线
│   ├── models/
│   │   ├── character.py     # 角色模型（含 xia_yi / title）
│   │   └── region.py        # 地区模型
│   ├── ai/
│   │   ├── agent.py         # AI 智能体
│   │   ├── llm.py           # LLM 调用（OpenAI）
│   │   └── memory.py        # NPC 记忆
│   └── api/
│       ├── world_api.py     # 世界 API
│       ├── npc_api.py       # NPC API
│       └── event_api.py     # 事件 API
├── data/
│   ├── chars.json           # 角色数据（35人）
│   └── treasures.json       # 宝物库（20件）
├── frontend/
│   └── index.html           # 前端界面（含所有弹窗/排序）
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/world` | 获取世界状态（回合、角色、玩家、好感度） |
| GET | `/api/start/candidates` | 获取初始选人候选（3人） |
| POST | `/api/start/select` | 选择角色 `{"name":"黄宇翔"}` |
| POST | `/tick` | 推进一回合 |
| GET | `/api/events/pending` | 获取待处理大事（拜师/结婚/结拜） |
| POST | `/api/events/decide` | 处理事件 |
| GET | `/api/events` | 获取江湖日志 |
| GET | `/api/tasks/pending` | 获取本回合任务列表 |
| POST | `/api/tasks/execute` | 执行任务 `{"task_id":0,"mode":"normal\|scheme\|focus"}` |
| GET | `/api/decay/pending` | 获取不进则退待选属性 |
| POST | `/api/decay/execute` | 选择降低属性 `{"field":"base_w"}` |
| GET | `/api/tournament` | 获取武道会对阵图及结果 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥（不设置时 NPC 默认 wait，游戏可正常运行） |

## 数据来源

角色数据来源于小说《浪子江湖》，包含 35 位角色。
