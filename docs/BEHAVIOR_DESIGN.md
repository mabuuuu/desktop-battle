# Desktop Battle - 行为设计文档

## 行为系统概述

单位的行为由**行为树 (Behavior Tree)** 驱动，使用 `py_trees` 实现。每个单位根据**角色 (Role)** 拥有独立的定制行为树实例，每2帧 (30Hz) tick一次。

阵营级别的决策通过**共享黑板 (Blackboard)** 协调，实现多单位协作。

**拟真系统** (`src/simulation/realism.py`) 管理单位心理状态（士气/情绪/犹豫），与行为树联动。

**感知系统** (`src/simulation/perception.py`) 限制单位信息获取范围，只有视野/感知内的事件才能触发行为。

**事件总线** (`src/simulation/events.py`) 管理事件传播，事件带位置属性，只在感知范围内传播。

## 角色行为树架构

每种角色有独立行为树，优先级不同:

### 生产者 (Gatherer) 行为树

```
Root (Selector)
├── 逃跑 (HP低 → FleeToBase)
├── 运送资源 (满载 → MoveToBase → Deposit)
├── 采集 (未满载 → MoveToResourceNode → Gather)
├── 制作 (有制作订单 → MoveToWorkbench → AtWorkbench → Craft)
├── 拾取武器 (空手+地上有武器 → MoveToWeapon → Equip)
└── 漫步 (Wander)
```

### 建造者 (Builder) 行为树

```
Root (Selector)
├── 逃跑 (HP低 → FleeToBase)
├── 建造 (有建造订单 → MoveToBuildSite → Build)
├── 制作 (有制作订单 → MoveToWorkbench → AtWorkbench → Craft)
├── 运送资源 (CarryingResources → MoveToBase → Deposit)
├── 辅助采集 (NeedResources → MoveToResourceNode → Gather)
├── 拾取武器
└── 漫步
```

### 战士 (Soldier) 行为树

```
Root (Selector)
├── 逃跑 (HP极低 → FleeToBase)
├── 求援 (Outnumbered → RequestHelp)
├── 攻击 (EnemyInAttackRange → ExecuteAttack)
├── 追击 (EnemyInSight → ChaseEnemy)  [感知系统限制]
├── 响应求援 (RespondToHelp)
├── 巡逻 (Patrol: 前线↔基地交替)
├── 拾取武器
├── 运送资源
└── 漫步
```

### 侦察 (Scout) 行为树

```
Root (Selector)
├── 逃跑 (HP低 → FleeToBase)
├── 侦察 (ScoutArea: 向敌方渗透→发现敌人→返回报告)
├── 攻击 (EnemyInAttackRange → ExecuteAttack)
├── 拾取武器
└── 巡逻
```

## 感知系统

### 视野配置

| 范围类型 | 距离 | 角度 | 说明 |
|---------|------|------|------|
| 前方视野 | 100 px | 120° 扇形 | 朝向方向的可见范围 |
| 身后感知 | 40 px | 360° 圆形 | 身后近距离可感知 |
| 听觉范围 | 60 px | 360° 圆形 | 全方向听觉 |

### 感知影响

- `EnemyInSight` 条件: 只检测**前方视野+身后感知**范围内的敌人
- 求援响应: 只有**感知到**求援者才会响应
- 事件传播: 事件带位置，只有在感知范围内的单位才能收到

## 阵营策略 (Blackboard)

### 黑板数据

```python
class FactionBlackboard:
    # 资源
    wood: int = 0
    ore: int = 0

    # 建造队列
    build_orders: list[BuildOrder] = []

    # 制作队列
    craft_orders: list[CraftOrder] = []

    # 战略
    strategy: str = "expand"     # expand / defend / attack
    rally_point: tuple[int, int] # 集结点
    threat_level: float = 0.0    # 0.0 ~ 1.0

    # 单位分配
    gatherers_needed: int = 3
    builders_needed: int = 1
    soldiers_needed: int = 2
```

### 策略决策规则

| 条件 | 策略 | 角色比例 |
|------|------|---------|
| 初始/资源不足 | expand | 3采集:1建造:1战士 |
| 人口>=6 | rush | 1采集:4战士:1侦察 |
| 人口<3 | defense | 2采集:1建造:2战士 |
| 木材>=30+矿石>=10 | tech | 2采集:2建造:1战士 |

### 动态角色分配

- 每次策略变更时，`auto_assign_roles` 重新计算角色需求
- 空闲单位优先分配到缺人角色
- 角色变更时**自动重建行为树**（`_rebuild_bt_if_role_changed`）

## 拟真系统

### 单位心理模型 (UnitMind)

| 属性 | 范围 | 说明 |
|------|------|------|
| 士气 (morale) | 0.0~1.0 | 受HP比例/友军数/敌军数影响 |
| 情绪 (emotion) | calm/alert/fearful/brave/hesitant | 由士气自动推算 |
| 犹豫计时 | 秒 | >0时处于犹豫状态 |
| 决策冷却 | 秒 | 防止频繁切换决策 |

### 求援行为

```
战士在战场劣势（敌军>友军+1）
  ↓
发出HelpRequest + HelpRequest事件
  ↓
感知范围内友军40%概率响应
  ↓
响应者决定: 去战场支援 / 回基地报信
```

### 犹豫行为

```
战士前往战场途中
  ↓
发现后方5+人从事生产
  ↓
20%概率犹豫1.5~3秒（30秒冷却期）
  ↓
犹豫结束 → 返回基地从事生产
```

避免所有人同时犹豫: 概率触发 + 决策冷却

## 事件总线

### 事件类型

| 类型 | 说明 | TTL |
|------|------|-----|
| HELP_REQUEST | 求援请求 | 15秒 |
| ENEMY_SPOTTED | 发现敌人 | 10秒 |
| UNDER_ATTACK | 遭受攻击 | 10秒 |
| BUILDING_COMPLETE | 建造完成 | 10秒 |
| RESOURCE_FOUND | 发现资源 | 10秒 |
| SCHISM_WARNING | 分裂预警 | 10秒 |
| CARRY_MATERIAL | 搬运材料 | 10秒 |

事件带位置属性(x,y)，只有感知范围内的单位能收到。

## 行为详细定义

### 采集行为 (GatherResources)

```
1. 移动到采集点 (移动速度 60px/s)
2. 到达后进入采集状态
3. 采集计时: 每秒获得 5 资源
4. 携带量满 (20) 或采集点被占 → 停止采集
5. 转为 ResourceDelivery 行为
```

### 运送行为 (DepositResources)

```
1. 移动回阵营仓库区域 (采集点附近)
2. 到达后自动存入资源
3. 清空携带量
4. 转为 ResourceGathering 或等待新指令
```

### 建造行为 (Build)

```
1. 确认资源充足 (黑板检查)
2. 移动到建造位置
3. 建造计时 (根据建筑类型)
4. 建造完成 → 建筑实体出现
5. 扣除阵营资源
```

### 制作行为 (CraftWeapon)

```
1. 确认资源充足
2. 移动到工具台旁
3. 制作计时 (根据武器类型)
4. 制作完成 → 武器出现在工具台旁
5. 扣除阵营资源
6. 附近空手单位自动拾取
```

### 战斗行为 (Combat)

```
1. 感知范围内发现敌方单位
2. 评估：敌我数量比、HP、武器
3. 决策：攻击 or 撤退
   - 攻击：移动到攻击范围 → 执行攻击 → 冷却 → 再攻击
   - 撤退：移动回基地方向
4. 战斗中每5秒重新评估
```

### 探索行为 (Explore/Wander)

```
1. 随机选择一个方向 (偏向敌方阵地)
2. 沿地面移动
3. 遇到窗口 → 有50%概率攀爬
4. 到达窗口顶部 → 站在窗口顶部观察
5. 观察范围扩大 (2倍感知范围)
6. 发现敌方 → 切换为战斗行为
7. 未发现 → 5秒后继续探索
```

### 攀爬行为 (Climb)

```
1. 检测前方有窗口边缘
2. 切换为 Kinematic 模式 (取消重力)
3. 沿窗口边框向上移动 (40px/s)
4. 到达窗口顶部 → 切换回 Dynamic
5. 站在窗口顶部边框上
```

### 逃跑行为 (Flee)

```
1. HP < 20% 时触发
2. 向远离敌人的方向移动 (速度 +20%)
3. 持续逃跑直到 HP 恢复到 30% (无自然恢复，需脱离战斗)
4. 逃跑中不攻击
5. 到达基地附近后转为 idle
```

## 行为优先级总结

### 战士行为树优先级

| 优先级 | 行为 | 触发条件 |
|--------|------|---------|
| 1 (最高) | 逃跑 | HP极低 |
| 2 | 求援 | 敌军多于友军 |
| 3 | 攻击 | 敌人在攻击范围内 |
| 4 | 追击 | 敌人在感知范围内 |
| 5 | 响应求援 | 感知到友军求援事件 |
| 6 | 巡逻 | 无更紧急任务 |
| 7 | 拾取武器 | 空手且地面有武器 |
| 8 | 运送资源 | 携带资源 |
| 9 (最低) | 漫步 | 无其他任务 |

## 动画驱动

- 动画从**帧计数**改为**时间连续驱动**（anim_time）
- 呼吸/行走/攻击等动画用连续sin函数，不再阶跃
- 行为树tick间隔: 2帧 (30Hz)
- 状态切换时有过渡混合（state_blend: ~7帧过渡）

## 行为日志

每个行为状态转换都记录到行为日志，详见 `LOGGING_DESIGN.md`。

日志格式：
```
[Unit:3 Red Warrior] State: idle → gathering | Target: WoodNode@1 | Pos: (120, 800)
[Unit:3 Red Warrior] State: gathering → delivering | Carried: 20 wood | Pos: (120, 800)
[Unit:7 Blue Warrior] State: exploring → chasing | Target: Unit:3 Red | Dist: 180px
```
