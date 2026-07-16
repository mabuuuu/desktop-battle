# Desktop Battle - 开发计�?
## 阶段划分

### Phase 0: 项目骨架 �?
**目标**：建立文档体系和项目基础结构

**交付�?*�?- [x] 全部设计文档
- [x] 项目目录结构
- [x] requirements.txt
- [x] .gitignore
- [x] Git 仓库初始�?
---

### Phase 1: 渲染与窗口基础

**目标**：在桌面上显示透明窗口，能绘制线条图形

**改动目标**�?1. 实现 `src/render/overlay.py` �?封装 transparent-overlay，配置窗口穿�?置顶
2. 实现 `src/desktop/taskbar.py` �?检测任务栏位置
3. 实现 `src/desktop/coord.py` �?坐标转换工具
4. 实现 `src/render/sprite.py` �?线条绘制工具（线段、圆、矩形）
5. 实现 `src/core/game_loop.py` �?主循环框架（帧率控制、暂停支持）
6. 实现 `src/core/config.py` �?Pydantic 配置模型
7. 实现 `src/ui/tray.py` �?系统托盘图标 + 右键菜单（暂�?继续、面板、设置、退出）
8. 实现 `src/main.py` �?入口，启动主循环 + 托盘
9. 验证：桌面上出现透明窗口，绘制一条测试线段在任务栏位置，托盘图标可见，右键菜单可�?
**预计改动文件**�?- `src/main.py` (新建)
- `src/core/game_loop.py` (新建)
- `src/core/config.py` (新建)
- `src/render/overlay.py` (新建)
- `src/render/sprite.py` (新建)
- `src/desktop/taskbar.py` (新建)
- `src/desktop/coord.py` (新建)
- `src/ui/tray.py` (新建)
- `src/ui/__init__.py` (新建)
- `requirements.txt` (更新)

---

### Phase 2: 物理引擎与地�?
**目标**：物理世界运行，任务栏和窗口作为地形

**改动目标**�?1. 实现 `src/physics/engine.py` �?pymunk 物理世界封装
2. 实现 `src/physics/terrain.py` �?任务栏地面物理体
3. 实现 `src/desktop/window_scanner.py` �?窗口枚举 �?平台物理�?4. 实现 `src/physics/body_factory.py` �?物理体创建工�?5. 集成物理更新到游戏循�?6. 验证：物理测试体在任务栏上受重力落下并停�?
**预计改动文件**�?- `src/physics/engine.py` (新建)
- `src/physics/terrain.py` (新建)
- `src/physics/body_factory.py` (新建)
- `src/desktop/window_scanner.py` (新建)
- `src/core/game_loop.py` (更新)
- `src/render/overlay.py` (更新，绘制地�?

---

### Phase 3: 单位实体与移�?
**目标**：火柴人在任务栏上行�?
**改动目标**�?1. 实现 `src/entity/unit.py` �?单位实体（属性、物理体、渲染）
2. 实现 `src/entity/faction.py` �?阵营管理
3. 实现火柴人绘制（线条人物 + 阵营色）
4. 实现单位移动（施加力、速度限制�?5. 实现单位着地检�?6. 验证�?个阵营各1个火柴人在任务栏上行�?
**预计改动文件**�?- `src/entity/unit.py` (新建)
- `src/entity/faction.py` (新建)
- `src/render/sprite.py` (更新，火柴人绘制)
- `src/physics/engine.py` (更新，碰撞回�?
- `src/core/game_loop.py` (更新)

---

### Phase 4: 资源与经济系�?
**目标**：资源采集点运作，单位采集和运送资�?
**改动目标**�?1. 实现 `src/entity/resource_node.py` �?资源采集点实�?2. 实现 `src/economy/resource.py` �?资源管理、阵营仓�?3. 实现采集点绘制（菱形 + 发光效果�?4. 实现资源携带可视化（头顶资源图标�?5. 验证：单位走到采集点 �?采集 �?走回基地 �?存入资源

**预计改动文件**�?- `src/entity/resource_node.py` (新建)
- `src/economy/resource.py` (新建)
- `src/entity/unit.py` (更新，携带资�?
- `src/render/sprite.py` (更新，采集点绘制)

---

### Phase 5: 建筑系统

**目标**：建造工具台和兵�?
**改动目标**�?1. 实现 `src/entity/building.py` �?建筑实体（工具台、兵营）
2. 实现 `src/economy/production.py` �?兵营生产队列
3. 实现建筑绘制（线条建�?+ 阵营色）
4. 实现建造流程（单位走到位置 �?建造计�?�?建筑出现�?5. 实现兵营自动生产单位
6. 验证：单位建造工具台 �?建造兵�?�?兵营生产新单�?
**预计改动文件**�?- `src/entity/building.py` (新建)
- `src/economy/production.py` (新建)
- `src/entity/unit.py` (更新)
- `src/render/sprite.py` (更新，建筑绘�?

---

### Phase 6: 武器与制作系�?
**目标**：工具台制作武器，单位装备武�?
**改动目标**�?1. 实现 `src/combat/weapon.py` �?武器定义与实�?2. 实现 `src/economy/crafting.py` �?制作系统
3. 实现武器绘制（附加在火柴人手臂上�?4. 实现武器掉落与拾�?5. 验证：单位在工具台制作长�?�?另一单位拾取 �?手持长矛行走

**预计改动文件**�?- `src/combat/weapon.py` (新建)
- `src/economy/crafting.py` (新建)
- `src/entity/unit.py` (更新，装备武�?
- `src/render/sprite.py` (更新，武器绘�?

---

### Phase 7: 行为树AI

**目标**：单位自动采集、建造、制作、探�?
**改动目标**�?1. 实现 `src/behavior/trees.py` �?行为树定�?2. 实现 `src/behavior/actions.py` �?动作节点
3. 实现 `src/behavior/conditions.py` �?条件节点
4. 实现 `src/behavior/blackboard.py` �?阵营共享黑板
5. 集成行为树到单位更新循环
6. 验证：单位自动采�?�?建造工具台 �?制作武器 �?探索

**预计改动文件**�?- `src/behavior/trees.py` (新建)
- `src/behavior/actions.py` (新建)
- `src/behavior/conditions.py` (新建)
- `src/behavior/blackboard.py` (新建)
- `src/entity/unit.py` (更新)
- `src/core/game_loop.py` (更新)

---

### Phase 8: 战斗系统

**目标**：单位发现敌人并战斗

**改动目标**�?1. 实现 `src/combat/damage.py` �?伤害计算（含随机浮动、减伤）
2. 实现 `src/combat/attack.pybat/attack.py` �?攻击执行（近战、击退�?3. 实现攻击动画（手臂挥动）
4. 实现血条显�?5. 实现死亡动画（倒下 + 透明化）
6. 实现战斗行为树节�?7. 验证：红蓝单位相�?�?战斗 �?一方死�?
**预计改动文件**�?- `src/combat/damage.py` (新建)
- `src/combat/attack.py` (新建)
- `src/render/effects.py` (新建，攻击闪光、死亡效�?
- `src/render/sprite.py` (更新，血�?
- `src/behavior/actions.py` (更新，战斗动�?
- `src/behavior/conditions.py` (更新，战斗条�?

---

### Phase 9: 攀爬与窗口交互

**目标**：单位攀爬窗口，在窗口顶部站�?
**改动目标**�?1. 实现攀爬物理（Kinematic切换、沿墙壁移动�?2. 实现攀爬动�?3. 实现窗口顶部站立
4. 实现从窗口跳�?5. 验证：单位走到窗口旁 �?攀�?�?站在窗口顶部 �?跳下

**预计改动文件**�?- `src/physics/engine.py` (更新，攀爬逻辑)
- `src/entity/unit.py` (更新，攀爬状�?
- `src/render/sprite.py` (更新，攀爬动�?
- `src/behavior/actions.py` (更新，攀爬动�?

---

### Phase 10: 日志系统

**目标**：完整的行为日志、系统日志、错误日�?
**改动目标**�?1. 实现 `src/logging/logger.py` �?LogManager
2. 实现 `src/logging/behavior_log.py` �?行为日志记录
3. 实现 `src/logging/system_log.py` �?系统日志记录
4. 实现 `src/logging/error_log.py` �?错误日志记录
5. 在所有模块中集成日志调用
6. 验证：运行游�?�?检�?logs/ 目录下三类日志文�?
**预计改动文件**�?- `src/logging/logger.py` (新建)
- `src/logging/behavior_log.py` (新建)
- `src/logging/system_log.py` (新建)
- `src/logging/error_log.py` (新建)
- 所有现有文�?(更新，添加日志调�?

---

### Phase 11: UI面板与设�?
**目标**：信息面板展示双方参数，设置对话框可调参�?
**改动目标**�?1. 实现 `src/ui/panel.py` �?信息面板（双方资�?单位/建筑/武器/策略实时展示�?2. 实现 `src/ui/settings.py` �?设置对话框（游戏速度、伤害倍率、显示选项等）
3. 实现面板拖拽和关�?4. 实现面板区域鼠标拦截（其他区域穿透）
5. 实现设置持久化（`%APPDATA%/DesktopBattle/settings.json`�?6. 集成面板数据刷新（每0.5秒从 World State 读取�?7. 验证：面板显示双方实时参数，可拖拽移动，设置修改生效

**预计改动文件**�?- `src/ui/panel.py` (新建)
- `src/ui/settings.py` (新建)
- `src/ui/tray.py` (更新，面�?设置菜单联动)
- `src/render/overlay.py` (更新，面板区域渲�?
- `src/core/config.py` (更新，设置持久化)

---

### Phase 12: 外部AI接入

**目标**：接入第三方AI API获取战斗策略

**改动目标**�?1. 实现 `src/ai/client.py` �?OpenAI兼容API客户端（httpx异步调用�?2. 实现 `src/ai/prompts.py` �?内置提示词模板（战况→策略JSON�?3. 实现 `src/ai/strategy.py` �?策略解析与执行（JSON→Blackboard写入�?4. 实现 `src/ai/strategy_log.py` �?AI策略日志（请�?响应/降级/切换�?5. 集成AI策略到阵营Blackboard（每15秒请求一次）
6. 实现降级策略（连续失败→规则策略�?7. 在设置对话框中增加AI配置项（apiKey/url/model/开关）
8. 验证：配置AI后，阵营策略由AI驱动，策略日志可�?
**预计改动文件**�?- `src/ai/client.py` (新建)
- `src/ai/prompts.py` (新建)
- `src/ai/strategy.py` (新建)
- `src/ai/strategy_log.py` (新建)
- `src/ai/__init__.py` (新建)
- `src/ui/settings.py` (更新，AI配置�?
- `src/core/config.py` (更新，AIConfig)
- `src/behavior/blackboard.py` (更新，AI策略写入)

---

### Phase 13: 整合与调优 ✅

**目标**：完整游戏循环运行，平衡性调优

**改动目标**：
1. 完整开局流程（2阵营、采集点、初始单位）
2. 完整经济循环（采集 → 建造 → 制作 → 生产）
3. 完整战斗循环（探索 → 发现 → 战斗 → 死亡 → 生产补充）
4. 性能优化（50+单位 @ 60fps）
5. 平衡性调优（战斗时长、资源速率）
6. 验证：完整对局从开局到一方全灭

---

### Phase 14: 阵营分裂机制 ✅

**目标**：一方全灭后胜利方内部矛盾积累→阵营分裂→新一轮战斗

**改动目标**：
1. 实现 `src/entity/schism.py` — SchismManager分裂管理器（矛盾积累/争吵/小冲突/分裂触发/资源点争夺）
2. 更新 `src/entity/faction.py` — 新增conflict_score属性/分裂冷却
3. 更新 `src/core/config.py` — 新增SchismConfig（触发人口/积累速率/分裂阈值/争夺概率/冷却时间）
4. 更新 `src/core/world.py` — 集成分裂检测到主循环
5. 更新 `src/behavior/trees.py` — 新增争吵状态UnitState.ARGUING
6. 更新 `src/render/sprite.py` — 叛军阵营颜色/争吵气泡(红色感叹号)
7. 更新 `src/entity/unit.py` — 新增UnitState.ARGUING
8. 更新 `src/game_logging/behavior_log.py` — 分裂相关日志
9. 验证：红方全灭蓝方→红方人口超15→矛盾积累→分裂→红方vs红方·叛军

**预计改动文件**：
- `src/entity/schism.py` (新建)
- `src/entity/faction.py` (更新)
- `src/core/config.py` (更新)
- `src/core/world.py` (更新)
- `src/behavior/trees.py` (更新)
- `src/render/sprite.py` (更新)
- `src/entity/unit.py` (更新)
- `src/game_logging/behavior_log.py` (更新)

---

### Phase 15: 关节式火柴人 + 速度可配置 ✅

**目标**：火柴人拥有膝关节和肘关节，动作更灵活自然

**改动目标**：
1. 重写 `src/render/sprite.py` draw_stickman为关节系统(肩→肘→手, 髋→膝→脚)
2. 提高默认移动速度(红方130/蓝方120)
3. 新增move_speed_multiplier可配置项
4. 验证：火柴人idle时手臂自然垂落，walking时腿交替摆动

---

### Phase 16: 中文化+面板缩放+设置弹窗+流畅度+行为树职责系统 ✅

**目标**：全面中文化、面板可缩放、设置弹窗、动画流畅度、角色行为树

**改动目标**：
1. InfoPanel/HUD中文化(使用overlay.draw_text)
2. InfoPanel右边缘拖拽缩放
3. tkinter设置弹窗(6个参数滑块)
4. 动画时间连续驱动+行为树tick间隔2帧
5. UnitRole枚举+每种角色独立行为树
6. 动态角色分配(按策略调整比例)
7. 验证：面板中文显示，设置弹窗可用，角色行为树工作

---

### Phase 17: 拟真系统+感知+事件+建筑组装+调试模式 ✅

**目标**：拟真行为(求援/犹豫)、感知系统、事件总线、建筑组装、调试模式

**改动目标**：
1. 视野感知系统(前方扇形+身后+听觉)
2. 拟真系统(士气/情绪/求援/犹豫)
3. 事件总线(位置感知事件传播)
4. 建筑组装系统(材料形状/零件清单/逐步拼装)
5. 调试模式(选中单位/指定行为/信息显示)
6. 血条移除
7. EnemyInSight改用感知系统
8. 战士行为树新增求援+响应分支
9. 验证：战士劣势求援，犹豫行为触发，调试模式可用
---

## 执行规则

1. 每个Phase开始前，更新本文档标记当前Phase
2. 每次代码改动前，先确认对应设计文档的规格
3. 每次改动完成后，更新 CHANGELOG.md
4. 每次改动提交 Git �?Push，提交信息格式：`[Phase N] 简述改动内容`
5. 一个Phase内的多次改动可以分多次提�?6. Phase完成后在本文档标�?�?
