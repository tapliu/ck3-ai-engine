# 浪子江湖 · 侠行四海

AI 驱动的武侠江湖模拟游戏。

## 快速开始

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

浏览器打开 `http://localhost:8000`

## 游戏玩法

1. **选人** — 开局从 3 个随机角色中选择你的侠客
2. **Tick** — 每点击一次推进一回合，NPC 会自主决策（战争、刺杀等）
3. **事件** — 触发拜师、结婚、结拜等人生大事，从 3 个候选中选择
4. **奇遇** — 每回合有概率获得宝物，属性随之成长

## 项目结构

```
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── core/
│   │   ├── world.py         # 世界状态 + 事件系统
│   │   ├── engine.py        # 游戏主循环
│   │   └── event_bus.py     # 事件总线
│   ├── models/
│   │   ├── character.py     # 角色模型
│   │   └── region.py        # 地区模型
│   ├── ai/
│   │   ├── agent.py         # AI 智能体
│   │   ├── llm.py           # LLM 调用（OpenAI）
│   │   └── memory.py        # NPC 记忆
│   ├── api/
│   │   ├── world_api.py     # 世界 API
│   │   ├── npc_api.py       # NPC API
│   │   └── event_api.py     # 事件 API
│   └── storage/
│       └── save_load.py     # 存档/读档
├── data/
│   ├── chars.json           # 角色数据（35人）
│   └── treasures.json       # 宝物库（20件）
├── frontend/
│   └── index.html           # 前端界面
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/world` | 获取世界状态（回合、角色、玩家） |
| GET | `/api/start/candidates` | 获取初始选人候选（3人） |
| POST | `/api/start/select` | 选择角色 `{"name":"黄宇翔"}` |
| POST | `/tick` | 推进一回合 |
| GET | `/api/events/pending` | 获取待处理事件 |
| POST | `/api/events/decide` | 处理事件 `{"event":"marry","target":"单钰莹"}` |
| GET | `/api/events` | 获取事件日志 |
| GET | `/api/npc/{name}` | 获取 NPC 详情 |

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥（不设置时 NPC 默认 wait） |

## 数据来源

角色数据来源于小说《浪子江湖》，包含 35 位角色，每人有武力、智谋、内力、魅力四项属性及年龄、描述。
