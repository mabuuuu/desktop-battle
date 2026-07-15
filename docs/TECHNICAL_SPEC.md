# Desktop Battle - 技术规格文档

## 技术栈

### 核心依赖

| 组件 | 库 | 版本 | 用途 |
|------|-----|------|------|
| 渲染层 | `transparent-overlay` | latest | 透明窗口 + `UpdateLayeredWindow` 逐像素Alpha渲染 |
| 窗口管理 | `pywin32` (win32gui/win32con) | >=305 | 窗口穿透、置顶、任务栏检测、窗口枚举 |
| 物理引擎 | `pymunk` | >=6.4 | 2D物理模拟（重力、碰撞、关节、摩擦力） |
| 数值计算 | `numpy` | >=1.24 | RGBA像素数组操作、向量运算 |
| 行为树 | `py_trees` | >=2.2 | AI行为树决策系统 |
| 日志 | `loguru` | >=0.7 | 结构化日志（系统日志、错误日志） |
| 配置 | `pydantic` | >=2.0 | 数据模型验证、配置管理 |
| 托盘图标 | `infi.systray` | >=0.1 | Windows系统托盘图标 + 右键菜单 |
| HTTP客户端 | `httpx` | >=0.27 | 外部AI API调用（OpenAI兼容接口） |

### 可选依赖（后期）

| 组件 | 库 | 用途 |
|------|-----|------|
| ML推理 | `onnxruntime` | 小型神经网络推理 |
| RL训练 | `stable-baselines3` | 强化学习训练 |
| 多智能体 | `pettingzoo` | 多智能体环境标准 |
| LLM策略 | `ollama` (HTTP) | 本地LLM策略决策 |

### 开发工具

| 工具 | 用途 |
|------|------|
| `pytest` | 单元测试 |
| `ruff` | 代码格式化 + lint |
| `basedpyright` | 类型检查 |
| `PyInstaller` | 打包为exe |

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Game Loop (60fps)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Physics  │→│ Behavior │→│  Combat  │→│ Render  │ │
│  │ Update   │  │ Update   │  │  Update  │  │ Update  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│       ↑              ↑             ↑            ↑        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              World State (ECS-like)               │   │
│  │  Units | Buildings | Resources | Projectiles     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
         ↑                              ↑
┌────────────────┐           ┌──────────────────────┐
│  Desktop Bridge │           │   Logging System     │
│  (pywin32)      │           │  System | Behavior   │
│  - 任务栏检测   │           │  | Error | Combat    │
│  - 窗口枚举     │           └──────────────────────┘
│  - 坐标转换     │
└────────────────┘
┌─────────────────────────────────────────────────────────┐
│                      UI Layer                            │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │ System Tray  │  │   Info Panel (半透明覆盖层)       │ │
│  │ - 托盘图标   │  │   - 双方资源/单位/建筑/战况       │ │
│  │ - 右键菜单   │  │   - 可拖拽、可关闭                │ │
│  └──────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 模块划分

```
src/
├── main.py                  # 入口
├── core/
│   ├── game_loop.py         # 主循环、帧率控制
│   ├── world.py             # 世界状态管理
│   └── config.py            # 全局配置 (Pydantic)
├── render/
│   ├── overlay.py           # transparent-overlay 封装
│   ├── sprite.py            # 精灵绘制（线条火柴人）
│   ├── camera.py            # 视口/坐标转换
│   └── effects.py           # 视觉效果（攻击闪光、死亡动画）
├── physics/
│   ├── engine.py            # pymunk 物理世界封装
│   ├── body_factory.py      # 物理体创建（单位、建筑、地形）
│   └── terrain.py           # 地形物理体（任务栏、窗口平台）
├── desktop/
│   ├── taskbar.py           # 任务栏位置/尺寸检测
│   ├── window_scanner.py    # 桌面窗口枚举 → 平台数据
│   └── coord.py             # 屏幕/世界坐标转换
├── entity/
│   ├── unit.py              # 单位实体
│   ├── building.py          # 建筑实体
│   ├── resource_node.py     # 资源采集点
│   ├── projectile.py        # 投射物
│   ├── faction.py           # 阵营管理
│   └── schism.py            # 阵营分裂管理器
├── behavior/
│   ├── trees.py             # 行为树定义
│   ├── actions.py           # 行为树动作节点
│   ├── conditions.py        # 行为树条件节点
│   └── blackboard.py        # 阵营共享黑板
├── combat/
│   ├── weapon.py            # 武器系统
│   ├── damage.py            # 伤害计算
│   └── attack.py            # 攻击执行
├── economy/
│   ├── resource.py          # 资源管理
│   ├── crafting.py          # 制作系统
│   └── production.py        # 兵营生产队列
├── ui/
│   ├── tray.py              # 系统托盘图标 + 右键菜单
│   ├── panel.py             # 信息面板（双方参数展示）
│   └── settings.py          # 设置对话框
├── ai/
│   ├── client.py            # 外部AI客户端（OpenAI兼容API）
│   ├── strategy.py          # AI策略解析与执行
│   ├── prompts.py           # 内置提示词模板
│   └── strategy_log.py      # AI策略日志
└── logging/
    ├── logger.py            # 日志管理器
    ├── behavior_log.py      # 行为日志
    ├── system_log.py        # 系统日志
    └── error_log.py         # 错误日志
```

## 渲染管线

### 渲染流程

```
每帧:
1. 清空 RGBA 缓冲区 (全透明)
2. 绘制地形 (任务栏、窗口平台) → 半透明线条
3. 绘制建筑 → 阵营色线条
4. 绘制资源采集点 → 闪烁效果
5. 绘制单位 → 阵营色火柴人 + 武器
6. 绘制投射物 → 运动轨迹
7. 绘制 HUD → 血条、资源数
8. 绘制效果 → 攻击闪光、死亡粒子
9. 调用 transparent-overlay.signal_render() 提交
```

### 坐标系

- **屏幕坐标**：左上角 (0,0)，Y轴向下，单位像素
- **物理坐标**：与屏幕坐标一致（pymunk Y轴向上，需翻转）
- **转换**：物理Y = 屏幕高度 - 屏幕Y

### 火柴人绘制规格

```
火柴人高度: 20px (可配置)
结构:
  头: 圆, 半径2px, 中心在 (0, -18)
  身: 线, (0, -16) → (0, -8)
  左臂: 线, (0, -14) → (-4, -10)
  右臂: 线, (0, -14) → (4, -10)  [持武器时延伸]
  左腿: 线, (0, -8) → (-3, 0)
  右腿: 线, (0, -8) → (3, 0)
  线宽: 1px
  颜色: 阵营主色
```

## 物理引擎

### pymunk 配置

```python
# 物理世界
space = pymunk.Space()
space.gravity = (0, 900)          # 向下重力 (像素/秒²)
space.damping = 0.9               # 全局阻尼
space.collision_slop = 0.5        # 碰撞容差

# 碰撞类型
COLLISION_TYPE = {
    "UNIT" = 1
COLLISION_TYPE "BUILDING" = 2
COLLISION_TYPE "TERRAIN" = 3
COLLISION_TYPE "RESOURCE" = 4
COLLISION_TYPE "PROJECTILE" = 5
COLLISION_TYPE "SENSOR" = 6       # 感知范围（不产生物理碰撞）
```

### 物理体类型

| 实体 | 物理体 | 形状 | 质量 | 说明 |
|------|--------|------|------|------|
| 单位 | Dynamic | 圆 (r=2) | 1.0 | 受重力、可推动 |
| 建筑 | Static | 多段线 | ∞ | 不可推动 |
| 地形 | Static | 线段 | ∞ | 任务栏、窗口边框 |
| 资源点 | Static | 圆 (r=4) | ∞ | 不可推动，有感知范围 |
| 投射物 | Dynamic | 圆 (r=2) | 0.1 | 高速、低重力影响 |

### 攀爬物理

单位攀爬窗口时：
1. 检测单位与窗口边框的接触
2. 进入"攀爬状态"时，将物理体改为 Kinematic，取消重力
3. 沿边框以固定速度移动
4. 到达窗口顶部时，切换为站在平台上（Dynamic + 平台碰撞）

## 帧率与时间步长

```python
TARGET_FPS = 60
PHYSICS_DT = 1.0 / 60.0          # 物理步长
RENDER_DT = 1.0 / 60.0           # 渲染步长
BEHAVIOR_TICK_INTERVAL = 3        # 行为树每3帧tick一次 (20Hz)
```

## 窗口管理

### 透明窗口设置

```python
# 窗口样式
WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST | WS_EX_TOOLWINDOW

# transparent-overlay 创建窗口后，通过 pywin32 追加:
# - WS_EX_TRANSPARENT: 点击穿透
# - WS_EX_TOPMOST: 始终置顶
# - WS_EX_TOOLWINDOW: 不出现在任务栏/Alt+Tab
```

### 部分点击穿透

后期鼠标交互时，需要动态切换穿透状态：
- 默认：全窗口穿透（`WS_EX_TRANSPARENT`）
- 鼠标悬停在单位上时：临时取消穿透，拦截点击
- 实现方式：每帧检测鼠标位置与单位碰撞，动态设置窗口样式

## 打包与分发

```bash
# PyInstaller 打包
pyinstaller --onefile --windowed --name "DesktopBattle" src/main.py

# 预期体积: ~15-20MB (含Python运行时 + pymunk + numpy)
```

## 系统托盘

### 技术实现

使用 `infi.systray` 创建 Windows 系统托盘图标。该库基于 Win32 `Shell_NotifyIcon` API，支持自定义图标和右键菜单。

### 托盘图标

- 图标：内置 ICO 资源（火柴人剪影，16x16）
- 悬停提示：`Desktop Battle - 桌面火柴人大乱斗`
- 双击：无操作（避免误触）

### 右键菜单

```
Desktop Battle
├── ▶ 继续 / ⏸ 暂停        # 切换游戏暂停/运行
├── ─────────────           # 分隔线
├── 📊 面板                  # 打开/关闭信息面板
├── ⚙️ 设置                  # 打开设置对话框
├── ─────────────           # 分隔线
└── ❌ 退出                  # 关闭程序
```

### 菜单项功能

| 菜单项 | 功能 | 实现 |
|--------|------|------|
| 继续/暂停 | 切换游戏主循环的暂停状态 | `game_loop.paused = not game_loop.paused` |
| 面板 | 切换信息面板的显示/隐藏 | `panel.visible = not panel.visible` |
| 设置 | 打开设置对话框 | 弹出独立窗口 |
| 退出 | 安全关闭程序 | 停止主循环 → 保存日志 → 退出 |

### 暂停行为

暂停时：
- 物理引擎停止更新
- 行为树停止 tick
- 渲染继续（画面冻结在最后一帧）
- 托盘菜单项切换为"▶ 继续"

## 信息面板

### 面板概述

信息面板是一个半透明的覆盖层窗口，显示双方阵营的实时参数。面板可拖拽、可关闭，不遮挡主要战斗区域。

### 面板布局

```
┌─────────────────────────────────────────┐
│  ⚔ Desktop Battle - 战况面板      [×]   │
├───────────────────┬─────────────────────┤
│   🔴 红方          │   🔵 蓝方           │
├───────────────────┼─────────────────────┤
│ 单位: 8/30        │ 单位: 6/30          │
│ 存活: 7           │ 存活: 5             │
│ 阵亡: 1           │ 阵亡: 3             │
├───────────────────┼─────────────────────┤
│ 木材: 45          │ 木材: 32            │
│ 矿石: 28          │ 矿石: 18            │
├───────────────────┼─────────────────────┤
│ 建筑:             │ 建筑:               │
│  工具台 Lv2 ×1    │  工具台 Lv1 ×1      │
│  兵营 ×1          │  兵营 ×1            │
├───────────────────┼─────────────────────┤
│ 武器:             │ 武器:               │
│  长矛 ×3          │  长矛 ×2            │
│  剑 ×1            │  盾 ×1              │
│  盾 ×2            │                     │
├───────────────────┼─────────────────────┤
│ 策略: expand      │ 策略: defend        │
│ 战斗中: 2人       │ 战斗中: 3人         │
│ 采集中: 3人       │ 采集中: 2人         │
│ 建造中: 1人       │ 探索中: 1人         │
│ 探索中: 1人       │ 空闲: 0人           │
│ 空闲: 0人         │                     │
├───────────────────┴─────────────────────┤
│  ⏱ 运行时间: 05:23  |  FPS: 58          │
└─────────────────────────────────────────┘
```

### 面板属性

| 属性 | 值 | 说明 |
|------|-----|------|
| 宽度 | 320 px | 固定宽度 |
| 高度 | 自适应 | 根据内容自动调整 |
| 背景色 | rgba(20, 20, 30, 200) | 深色半透明 |
| 边框色 | rgba(100, 100, 120, 180) | 浅灰半透明 |
| 字体 | Consolas 12px | 等宽字体 |
| 位置 | 屏幕右上角 | 默认位置，可拖拽 |
| 更新频率 | 每0.5秒 | 面板数据刷新频率 |

### 面板交互

- **拖拽**：按住标题栏拖拽移动面板位置
- **关闭**：点击 [×] 关闭面板（可通过托盘菜单重新打开）
- **穿透**：面板区域外的鼠标事件穿透到桌面

### 面板渲染方式

面板使用独立的 `transparent-overlay` 渲染，与游戏主覆盖层分开：
- 游戏覆盖层：全屏，点击穿透
- 面板覆盖层：面板区域大小，可拦截鼠标事件

或者：面板区域在主覆盖层上绘制，通过动态切换 `WS_EX_TRANSPARENT` 实现面板区域可点击、其他区域穿透。

**推荐方案**：在主覆盖层上绘制面板，面板区域通过命中测试动态取消穿透。实现更简单，避免多窗口管理。

## 设置对话框

### 设置项

| 设置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| 游戏速度 | 滑块 | 1.0x | 0.5x ~ 3.0x |
| 初始单位数 | 数字 | 5 | 每阵营 1~10 |
| 最大单位数 | 数字 | 30 | 每阵营 10~50 |
| 兵营生产间隔 | 数字 | 30秒 | 10~120秒 |
| 伤害倍率 | 滑块 | 1.0x | 0.5x ~ 2.0x |
| 显示血条 | 开关 | 开 | 是否显示单位血条 |
| 显示面板 | 开关 | 开 | 是否默认显示信息面板 |
| 日志级别 | 下拉 | INFO | DEBUG/INFO/WARNING/ERROR |

### 设置持久化

设置保存到 `%APPDATA%/DesktopBattle/settings.json`，启动时自动加载。

## 外部AI接入模块

### 概述

外部AI模块允许通过 OpenAI 兼容 API 接入第三方大语言模型，为每个阵营提供高层战略决策。AI 不控制逐帧行为，而是每隔一定时间输出策略指令，由行为树执行。

### 架构

```
┌─────────────────────────────────────────────┐
│              AI Strategy Layer               │
│                                              │
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │ AI Client   │    │ Strategy Parser     │ │
│  │ (httpx)     │───→│ (JSON → 指令)       │ │
│  │ apiKey+url  │    │                     │ │
│  └─────────────┘    └─────────┬───────────┘ │
│                               │              │
│  ┌─────────────┐              │              │
│  │ Prompts     │              ▼              │
│  │ (内置模板)  │    ┌─────────────────────┐ │
│  └─────────────┘    │ Blackboard Writer   │ │
│                     │ (写入阵营黑板)      │ │
│                     └─────────────────────┘ │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │ Strategy Log (策略日志)                  │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### AI客户端配置

```python
class AIConfig(BaseModel):
    enabled: bool = False              # 是否启用AI策略
    api_key: str = ""                  # API密钥
    api_url: str = "https://api.openai.com/v1/chat/completions"  # API端点
    model: str = "gpt-4o-mini"         # 模型名称
    strategy_interval: float = 15.0    # 策略请求间隔(秒)
    max_tokens: int = 500              # 单次请求最大token
    temperature: float = 0.7           # 生成温度
    timeout: float = 10.0              # 请求超时(秒)
```

### 提示词模板

系统提示词（内置，可自定义）：

```
你是一个桌面火柴人战斗游戏的阵营指挥官。你控制{faction_name}阵营。

当前战况：
- 我方单位: {unit_count} (存活{alive}, 阵亡{dead})
- 我方资源: 木材{wood}, 矿石{ore}
- 我方建筑: {buildings}
- 我方武器: {weapons}
- 敌方单位: {enemy_count}
- 敌方建筑: {enemy_buildings}
- 当前策略: {current_strategy}
- 单位分配: 采集{gatherers} 建造{builders} 战斗{soldiers} 探索{scouts}

请输出JSON格式的策略指令：
{
  "strategy": "expand|defend|attack|retreat",
  "priority": "economy|military|explore",
  "build_order": "workbench_lv1|workbench_lv2|barracks|none",
  "craft_order": "spear|sword|shield|none",
  "gatherer_count": <number>,
  "soldier_count": <number>,
  "scout_count": <number>,
  "reasoning": "<简短说明>"
}
```

### 策略执行流程

```
1. 每15秒触发一次AI请求
2. 收集阵营状态数据 → 填充提示词模板
3. 调用API → 获取JSON策略响应
4. 解析JSON → 写入阵营Blackboard
5. 行为树在下次tick时读取新策略
6. 记录策略日志
```

### 降级策略

- AI请求失败 → 保持当前策略不变
- 连续3次失败 → 切换为内置规则策略
- AI响应格式错误 → 解析失败时保持当前策略
- 超时 → 10秒超时，不阻塞主循环

### AI策略日志

| 事件 | 格式 |
|------|------|
| 请求发送 | `[AI:Red] Request sent | Model: gpt-4o-mini | Prompt tokens: ~200` |
| 策略接收 | `[AI:Red] Strategy: attack | Priority: military | Build: barracks | Craft: sword | Reasoning: "敌弱我强，应主动进攻"` |
| 请求失败 | `[AI:Red] Request failed: timeout | Fallback: keep current strategy` |
| 策略切换 | `[AI:Red] Strategy changed: expand → attack | Reason: enemy spotted` |
| 降级触发 | `[AI:Red] Fallback to rule-based | Consecutive failures: 3` |

策略日志输出到 `logs/strategy/` 目录，保留7天。
