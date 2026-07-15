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
│   └── faction.py           # 阵营管理
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
火柴人高度: 40px (可配置)
结构:
  头: 圆, 半径4px, 中心在 (0, -36)
  身: 线, (0, -32) → (0, -16)
  左臂: 线, (0, -28) → (-8, -20)
  右臂: 线, (0, -28) → (8, -20)  [持武器时延伸]
  左腿: 线, (0, -16) → (-6, 0)
  右腿: 线, (0, -16) → (6, 0)
  线宽: 2px
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
| 单位 | Dynamic | 圆 (r=4) | 1.0 | 受重力、可推动 |
| 建筑 | Static | 多段线 | ∞ | 不可推动 |
| 地形 | Static | 线段 | ∞ | 任务栏、窗口边框 |
| 资源点 | Static | 圆 (r=8) | ∞ | 不可推动，有感知范围 |
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
