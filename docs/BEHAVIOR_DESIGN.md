# Desktop Battle - 行为设计文档

## 行为系统概述

单位的行为由**行为树 (Behavior Tree)** 驱动，使用 `py_trees` 实现。每个单位拥有一个独立的行为树实例，每3帧 (20Hz) tick一次。

阵营级别的决策通过**共享黑板 (Blackboard)** 协调，实现多单位协作。

## 行为树架构

### 三层架构

```
Layer 1: 阵营策略 (Blackboard 共享)
  ↓ 写入策略目标
Layer 2: 单位行为树 (每单位独立)
  ↓ 产生动作
Layer 3: 动作执行 (物理/动画)
```

### 单位行为树结构

```
Root (Selector - 优先级从上到下)
│
├── Survival (Sequence)                    # 生存 — 最高优先级
│   ├── Condition: HP < 20%
│   └── Action: FleeToBase()
│
├── Combat (Selector)                      # 战斗 — 第二优先级
│   ├── MeleeAttack (Sequence)
│   │   ├── Condition: EnemyInAttackRange()
│   │   └── Action: ExecuteAttack()
│   ├── ChaseEnemy (Sequence)
│   │   ├── Condition: EnemyInSight()
│   │   └── Action: MoveTowardEnemy()
│   └── ReturnToFormation (Sequence)
│       ├── Condition: CombatDone()
│       └── Action: MoveToRallyPoint()
│
├── Construction (Sequence)                # 建造 — 第三优先级
│   ├── Condition: HasBuildOrder()
│   ├── Condition: HasResources()
│   ├── Action: MoveToBuildSite()
│   └── Action: Build()
│
├── Crafting (Sequence)                    # 制作 — 第四优先级
│   ├── Condition: HasCraftOrder()
│   ├── Condition: AtWorkbench()
│   └── Action: CraftWeapon()
│
├── ResourceDelivery (Sequence)            # 资源运送 — 第五优先级
│   ├── Condition: CarryingResources()
│   ├── Action: MoveToBase()
│   └── Action: DepositResources()
│
├── ResourceGathering (Sequence)           # 资源采集 — 第六优先级
│   ├── Condition: NeedResources()
│   ├── Condition: NotCarryingFull()
│   ├── Action: MoveToResourceNode()
│   └── Action: GatherResources()
│
├── PickupWeapon (Sequence)                # 拾取武器
│   ├── Condition: NoWeaponEquipped()
│   ├── Condition: WeaponOnGround()
│   ├── Action: MoveToWeapon()
│   └── Action: EquipWeapon()
│
└── Explore (Sequence)                     # 探索 — 最低优先级
    ├── Condition: NoHigherPriorityTask()
    └── Action: Wander()
```

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

| 条件 | 策略 | 行为 |
|------|------|------|
| 初始阶段 (前60秒) | expand | 优先采集 → 建造工具台 → 制作武器 |
| 发现敌方 | engage | 分配战斗单位追击 |
| 敌方接近基地 | defend | 全体回防 |
| 我方单位 > 敌方 1.5倍 | attack | 全体进攻 |
| 资源充足且无威胁 | expand | 继续发展经济 |

### 单位角色分配

阵营根据当前策略自动分配单位角色：

| 角色 | 行为 | 优先获得武器 |
|------|------|------------|
| 采集者 (Gatherer) | 采集 → 运送 → 采集循环 | 否 |
| 建造者 (Builder) | 响应建造/制作订单 | 否 |
| 战士 (Soldier) | 巡逻 → 发现敌人 → 战斗 | 是 |
| 探索者 (Scout) | 远距离探索 | 是 |

分配逻辑：
- 初始5人：3采集者 + 1建造者 + 1探索者
- 武器优先给战士和探索者
- 新生产的单位根据策略需求分配角色

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

| 优先级 | 行为 | 触发条件 |
|--------|------|---------|
| 1 (最高) | 逃跑 | HP < 20% |
| 2 | 战斗-攻击 | 敌人在攻击范围内 |
| 3 | 战斗-追击 | 敌人在视野内 |
| 4 | 建造 | 有建造订单且有资源 |
| 5 | 制作 | 有制作订单且在工具台旁 |
| 6 | 运送资源 | 携带资源已满 |
| 7 | 采集资源 | 需要资源且携带未满 |
| 8 | 拾取武器 | 空手且地面有武器 |
| 9 (最低) | 探索 | 无更高优先级任务 |

## 行为日志

每个行为状态转换都记录到行为日志，详见 `LOGGING_DESIGN.md`。

日志格式：
```
[Unit:3 Red Warrior] State: idle → gathering | Target: WoodNode@1 | Pos: (120, 800)
[Unit:3 Red Warrior] State: gathering → delivering | Carried: 20 wood | Pos: (120, 800)
[Unit:7 Blue Warrior] State: exploring → chasing | Target: Unit:3 Red | Dist: 180px
```
