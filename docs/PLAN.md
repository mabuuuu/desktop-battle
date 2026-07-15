# Desktop Battle - 开发计划

## 阶段划分

### Phase 0: 项目骨架 ✅

**目标**：建立文档体系和项目基础结构

**交付物**：
- [x] 全部设计文档
- [x] 项目目录结构
- [x] requirements.txt
- [x] .gitignore
- [x] Git 仓库初始化

---

### Phase 1: 渲染与窗口基础

**目标**：在桌面上显示透明窗口，能绘制线条图形

**改动目标**：
1. 实现 `src/render/overlay.py` — 封装 transparent-overlay，配置窗口穿透/置顶
2. 实现 `src/desktop/taskbar.py` — 检测任务栏位置
3. 实现 `src/desktop/coord.py` — 坐标转换工具
4. 实现 `src/render/sprite.py` — 线条绘制工具（线段、圆、矩形）
5. 实现 `src/core/game_loop.py` — 主循环框架（帧率控制）
6. 实现 `src/core/config.py` — Pydantic 配置模型
7. 实现 `src/main.py` — 入口，启动主循环
8. 验证：桌面上出现透明窗口，绘制一条测试线段在任务栏位置

**预计改动文件**：
- `src/main.py` (新建)
- `src/core/game_loop.py` (新建)
- `src/core/config.py` (新建)
- `src/render/overlay.py` (新建)
- `src/render/sprite.py` (新建)
- `src/desktop/taskbar.py` (新建)
- `src/desktop/coord.py` (新建)
- `requirements.txt` (更新)

---

### Phase 2: 物理引擎与地形

**目标**：物理世界运行，任务栏和窗口作为地形

**改动目标**：
1. 实现 `src/physics/engine.py` — pymunk 物理世界封装
2. 实现 `src/physics/terrain.py` — 任务栏地面物理体
3. 实现 `src/desktop/window_scanner.py` — 窗口枚举 → 平台物理体
4. 实现 `src/physics/body_factory.py` — 物理体创建工厂
5. 集成物理更新到游戏循环
6. 验证：物理测试体在任务栏上受重力落下并停住

**预计改动文件**：
- `src/physics/engine.py` (新建)
- `src/physics/terrain.py` (新建)
- `src/physics/body_factory.py` (新建)
- `src/desktop/window_scanner.py` (新建)
- `src/core/game_loop.py` (更新)
- `src/render/overlay.py` (更新，绘制地形)

---

### Phase 3: 单位实体与移动

**目标**：火柴人在任务栏上行走

**改动目标**：
1. 实现 `src/entity/unit.py` — 单位实体（属性、物理体、渲染）
2. 实现 `src/entity/faction.py` — 阵营管理
3. 实现火柴人绘制（线条人物 + 阵营色）
4. 实现单位移动（施加力、速度限制）
5. 实现单位着地检测
6. 验证：2个阵营各1个火柴人在任务栏上行走

**预计改动文件**：
- `src/entity/unit.py` (新建)
- `src/entity/faction.py` (新建)
- `src/render/sprite.py` (更新，火柴人绘制)
- `src/physics/engine.py` (更新，碰撞回调)
- `src/core/game_loop.py` (更新)

---

### Phase 4: 资源与经济系统

**目标**：资源采集点运作，单位采集和运送资源

**改动目标**：
1. 实现 `src/entity/resource_node.py` — 资源采集点实体
2. 实现 `src/economy/resource.py` — 资源管理、阵营仓库
3. 实现采集点绘制（菱形 + 发光效果）
4. 实现资源携带可视化（头顶资源图标）
5. 验证：单位走到采集点 → 采集 → 走回基地 → 存入资源

**预计改动文件**：
- `src/entity/resource_node.py` (新建)
- `src/economy/resource.py` (新建)
- `src/entity/unit.py` (更新，携带资源)
- `src/render/sprite.py` (更新，采集点绘制)

---

### Phase 5: 建筑系统

**目标**：建造工具台和兵营

**改动目标**：
1. 实现 `src/entity/building.py` — 建筑实体（工具台、兵营）
2. 实现 `src/economy/production.py` — 兵营生产队列
3. 实现建筑绘制（线条建筑 + 阵营色）
4. 实现建造流程（单位走到位置 → 建造计时 → 建筑出现）
5. 实现兵营自动生产单位
6. 验证：单位建造工具台 → 建造兵营 → 兵营生产新单位

**预计改动文件**：
- `src/entity/building.py` (新建)
- `src/economy/production.py` (新建)
- `src/entity/unit.py` (更新)
- `src/render/sprite.py` (更新，建筑绘制)

---

### Phase 6: 武器与制作系统

**目标**：工具台制作武器，单位装备武器

**改动目标**：
1. 实现 `src/combat/weapon.py` — 武器定义与实例
2. 实现 `src/economy/crafting.py` — 制作系统
3. 实现武器绘制（附加在火柴人手臂上）
4. 实现武器掉落与拾取
5. 验证：单位在工具台制作长矛 → 另一单位拾取 → 手持长矛行走

**预计改动文件**：
- `src/combat/weapon.py` (新建)
- `src/economy/crafting.py` (新建)
- `src/entity/unit.py` (更新，装备武器)
- `src/render/sprite.py` (更新，武器绘制)

---

### Phase 7: 行为树AI

**目标**：单位自动采集、建造、制作、探索

**改动目标**：
1. 实现 `src/behavior/trees.py` — 行为树定义
2. 实现 `src/behavior/actions.py` — 动作节点
3. 实现 `src/behavior/conditions.py` — 条件节点
4. 实现 `src/behavior/blackboard.py` — 阵营共享黑板
5. 集成行为树到单位更新循环
6. 验证：单位自动采集 → 建造工具台 → 制作武器 → 探索

**预计改动文件**：
- `src/behavior/trees.py` (新建)
- `src/behavior/actions.py` (新建)
- `src/behavior/conditions.py` (新建)
- `src/behavior/blackboard.py` (新建)
- `src/entity/unit.py` (更新)
- `src/core/game_loop.py` (更新)

---

### Phase 8: 战斗系统

**目标**：单位发现敌人并战斗

**改动目标**：
1. 实现 `src/combat/damage.py` — 伤害计算（含随机浮动、减伤）
2. 实现 `src/combat/attack.pybat/attack.py` — 攻击执行（近战、击退）
3. 实现攻击动画（手臂挥动）
4. 实现血条显示
5. 实现死亡动画（倒下 + 透明化）
6. 实现战斗行为树节点
7. 验证：红蓝单位相遇 → 战斗 → 一方死亡

**预计改动文件**：
- `src/combat/damage.py` (新建)
- `src/combat/attack.py` (新建)
- `src/render/effects.py` (新建，攻击闪光、死亡效果)
- `src/render/sprite.py` (更新，血条)
- `src/behavior/actions.py` (更新，战斗动作)
- `src/behavior/conditions.py` (更新，战斗条件)

---

### Phase 9: 攀爬与窗口交互

**目标**：单位攀爬窗口，在窗口顶部站立

**改动目标**：
1. 实现攀爬物理（Kinematic切换、沿墙壁移动）
2. 实现攀爬动画
3. 实现窗口顶部站立
4. 实现从窗口跳下
5. 验证：单位走到窗口旁 → 攀爬 → 站在窗口顶部 → 跳下

**预计改动文件**：
- `src/physics/engine.py` (更新，攀爬逻辑)
- `src/entity/unit.py` (更新，攀爬状态)
- `src/render/sprite.py` (更新，攀爬动画)
- `src/behavior/actions.py` (更新，攀爬动作)

---

### Phase 10: 日志系统

**目标**：完整的行为日志、系统日志、错误日志

**改动目标**：
1. 实现 `src/logging/logger.py` — LogManager
2. 实现 `src/logging/behavior_log.py` — 行为日志记录
3. 实现 `src/logging/system_log.py` — 系统日志记录
4. 实现 `src/logging/error_log.py` — 错误日志记录
5. 在所有模块中集成日志调用
6. 验证：运行游戏 → 检查 logs/ 目录下三类日志文件

**预计改动文件**：
- `src/logging/logger.py` (新建)
- `src/logging/behavior_log.py` (新建)
- `src/logging/system_log.py` (新建)
- `src/logging/error_log.py` (新建)
- 所有现有文件 (更新，添加日志调用)

---

### Phase 11: 整合与调优

**目标**：完整游戏循环运行，平衡性调优

**改动目标**：
1. 完整开局流程（2阵营、采集点、初始单位）
2. 完整经济循环（采集 → 建造 → 制作 → 生产）
3. 完整战斗循环（探索 → 发现 → 战斗 → 死亡 → 生产补充）
4. HUD 显示（阵营资源、单位数、战况）
5. 性能优化（50+单位 @ 60fps）
6. 平衡性调优（战斗时长、资源速率）
7. 验证：完整对局从开局到一方全灭

---

## 执行规则

1. 每个Phase开始前，更新本文档标记当前Phase
2. 每次代码改动前，先确认对应设计文档的规格
3. 每次改动完成后，更新 CHANGELOG.md
4. 每次改动提交 Git 并 Push，提交信息格式：`[Phase N] 简述改动内容`
5. 一个Phase内的多次改动可以分多次提交
6. Phase完成后在本文档标记 ✅
