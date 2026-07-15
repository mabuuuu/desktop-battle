# Desktop Battle - 变更日志

## 格式

```
## [日期] - 变更类型
### 变更内容
- 具体变更描述
```

---

## [2026-07-15] - 初始化

### 文档创建
- 创建 `PROJECT_OVERVIEW.md` — 项目总览、核心玩法、文档驱动流程
- 创建 `TECHNICAL_SPEC.md` — 技术栈、系统架构、渲染管线、物理引擎
- 创建 `UNIT_DESIGN.md` — 单位属性、阵营区分、外观绘制、生命周期
- 创建 `WEAPON_DESIGN.md` — 武器列表、制作链、伤害平衡、资源类型
- 创建 `BUILDING_DESIGN.md` — 建筑列表、建造流程、经济系统
- 创建 `BEHAVIOR_DESIGN.md` — 行为树架构、阵营策略、行为定义
- 创建 `PHYSICS_DESIGN.md` — 物理引擎、碰撞系统、地形、攀爬
- 创建 `LOGGING_DESIGN.md` — 日志系统、行为日志、系统日志、错误日志
- 创建 `CHANGELOG.md` — 变更日志
- 创建 `PLAN.md` — 阶段开发计划

### 项目初始化
- 创建项目目录结构 `src/`
- 创建 `requirements.txt`
- 创建 `.gitignore`

---

## [2026-07-15] - 需求补充：托盘图标 + 信息面板

### 文档更新
- 更新 `PROJECT_OVERVIEW.md` — V1范围增加托盘图标、右键菜单、信息面板、设置对话框
- 更新 `TECHNICAL_SPEC.md` — 新增 `infi.systray` 依赖、UI Layer 架构图、`src/ui/` 模块（tray/panel/settings）、系统托盘详细设计、信息面板布局与交互、设置对话框规格
- 更新 `PLAN.md` — Phase 1 增加托盘图标，Phase 11 增加面板和设置

---

## [2026-07-15] - 需求补充：外部AI接入

### 文档更新
- 更新 `TECHNICAL_SPEC.md` — 新增 `httpx` 依赖、`src/ai/` 模块（client/strategy/prompts/strategy_log）、外部AI接入详细设计（架构/配置/提示词/执行流程/降级/策略日志）
- 更新 `PLAN.md` — 新增 Phase 12 外部AI接入，原 Phase 12 整合调优顺延为 Phase 13

---

## [2026-07-15] - Phase 1-6 代码实现

### 新增文件 (21个)
- `src/core/config.py` — GameConfig/AIConfig/FactionConfig (Pydantic)
- `src/core/game_loop.py` — 60fps主循环 (暂停/物理/行为/渲染调度)
- `src/core/world.py` — 世界状态管理 (阵营/单位/建筑/资源/物理/渲染)
- `src/render/overlay.py` — transparent-overlay封装 (透明/穿透/置顶)
- `src/render/sprite.py` — numpy RGBA绘制 (线条/圆/矩形/文本/火柴人/血条)
- `src/desktop/taskbar.py` — Win32任务栏位置检测
- `src/desktop/coord.py` — pymunk↔屏幕坐标转换
- `src/desktop/window_scanner.py` — EnumWindows→窗口平台物理体
- `src/physics/engine.py` — pymunk Space封装 (碰撞类型1-7)
- `src/physics/body_factory.py` — 物理体工厂
- `src/physics/terrain.py` — 任务栏地面物理体
- `src/entity/unit.py` — 单位实体 (HP1000/状态/移动/武器/渲染)
- `src/entity/faction.py` — 阵营管理 (仓库/单位/建筑)
- `src/entity/building.py` — 建筑实体 (工具台/兵营)
- `src/entity/resource_node.py` — 资源采集点
- `src/combat/weapon.py` — 武器定义 (徒手/长矛/剑/盾)
- `src/economy/resource.py` — 资源管理
- `src/economy/crafting.py` — 制作系统
- `src/economy/production.py` — 兵营生产队列
- `src/ui/tray.py` — 系统托盘+右键菜单
- `src/main.py` — 入口

---

## [2026-07-15] - Phase 7-13 代码实现

### 新增文件 (19个)
- `src/behavior/blackboard.py` — FactionBlackboard (策略/订单/角色分配)
- `src/behavior/conditions.py` — 10个py_trees条件节点
- `src/behavior/actions.py` — 15个py_trees动作节点
- `src/behavior/trees.py` — 9层优先级行为树
- `src/combat/damage.py` — 伤害计算 (随机浮动/盾减伤/倍率)
- `src/combat/attack.py` — 近战攻击执行
- `src/render/effects.py` — 攻击闪光/死亡粒子/浮动伤害数字
- `src/physics/climbing.py` — 攀爬物理 (KINEMATIC切换)
- `src/game_logging/logger.py` — LogManager (loguru三通道)
- `src/game_logging/behavior_log.py` — 行为日志
- `src/game_logging/system_log.py` — 系统日志
- `src/game_logging/error_log.py` — 错误日志
- `src/ui/panel.py` — InfoPanel (双方参数/拖拽/关闭)
- `src/ui/settings.py` — SettingsManager (持久化)
- `src/ai/client.py` — AIClient (httpx, OpenAI兼容API)
- `src/ai/prompts.py` — 内置提示词模板
- `src/ai/strategy.py` — AIStrategyManager (15秒请求/降级)
- `src/ai/strategy_log.py` — AI策略日志

### 更新文件 (5个)
- `src/core/world.py` — 集成行为树/攀爬/战斗/AI/面板/日志
- `src/core/game_loop.py` — 行为树+日志集成
- `src/main.py` — 完整启动流程
- `src/ui/tray.py` — 面板/设置联动
- `src/render/sprite.py` — 全状态动画

---

## [2026-07-15] - 全局尺寸缩小 (0.5x)

### 变更原因
火柴人高度从40px缩小到20px，所有单位和建筑等比缩小0.5倍

### 代码变更
- `src/core/config.py` — stickman_height 40→20, stickman_line_width 2→1, stickman_head_radius 4→2, unit_radius 4→2, unit_perception_range 200→100, building_spacing 20→10
- `src/combat/weapon.py` — attack_range全部÷2 (徒手20→10, 长矛45→22, 剑30→15, 盾15→8), visual_length全部÷2
- `src/combat/attack.py` — 默认徒手范围 20→10
- `src/behavior/conditions.py` — 默认徒手范围 20→10
- `src/entity/unit.py` — 默认perception_range 200→100, 血条宽度20→10, 血条高度3→2, 资源标记圆r=3→1.5
- `src/entity/building.py` — 工具台width 30→15 height 20→10, 兵营width 40→20 height 30→15
- `src/render/sprite.py` — draw_stickman所有偏移量÷2 (body/body_top/head/arm_root/leg/arm端点/动画偏移量全部缩放)

### 文档变更
- `docs/TECHNICAL_SPEC.md` — 火柴人绘制规格更新, 单位r=2, 资源点r=4
- `docs/UNIT_DESIGN.md` — 火柴人结构20px, 体型半径2px, 感知100px, 攻击10px, 盾r=2.5
- `docs/WEAPON_DESIGN.md` — 全部武器攻击范围÷2, 视觉长度÷2, 盾r=2.5
- `docs/BUILDING_DESIGN.md` — 采集点10x8, 工具台15x10, 兵营20x15, 防御塔10x25
- `docs/PHYSICS_DESIGN.md` — 碰撞体半径2px
