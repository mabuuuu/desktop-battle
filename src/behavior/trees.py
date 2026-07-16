"""Desktop Battle - 行为树构建器.

为不同职责角色创建独立行为树:
- 生产者 (gatherer): 采集→运送→制作
- 建造者 (builder): 建造→制作→辅助采集
- 战士 (soldier): 巡逻→追击→攻击→逃跑
- 侦察 (scout): 探索→预警→骚扰
- 空闲 (idle): 通用行为树（原9层优先级）

角色动态分配: 空闲单位按需分配，战斗中根据策略调整。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import py_trees

from src.behavior.actions import (
    Build,
    ChaseEnemy,
    CraftWeapon,
    DepositResources,
    EquipWeapon,
    ExecuteAttack,
    FleeToBase,
    GatherResources,
    MoveToBase,
    MoveToBuildSite,
    MoveToResourceNode,
    MoveToWeapon,
    MoveTowardEnemy,
    Patrol,
    ScoutArea,
    Wander,
)
from src.behavior.conditions import (
    AtWorkbench,
    CarryingResources,
    EnemyInAttackRange,
    EnemyInSight,
    HasBuildOrder,
    HasCraftOrder,
    HPCheck,
    IsGatherer,
    IsBuilder,
    IsSoldier,
    IsScout,
    NeedResources,
    NoWeaponEquipped,
    WeaponOnGround,
)

if TYPE_CHECKING:
    pass


def create_gatherer_behavior_tree(unit_name: str = "Gatherer") -> py_trees.behaviour.Behaviour:
    """创建生产者行为树.

    优先级:
    1. 逃跑 (HP低)
    2. 运送资源 (满载→回基地)
    3. 采集 (未满载→采集点→采集)
    4. 制作 (有制作订单)
    5. 拾取武器
    6. 漫步
    """
    root = py_trees.composites.Selector(name=f"{unit_name}_Gatherer", memory=False)

    # 1. 逃跑
    flee_seq = py_trees.composites.Sequence(name="Flee", memory=True)
    flee_seq.add_child(HPCheck(name="HP_Low"))
    flee_seq.add_child(FleeToBase(name="Flee"))
    root.add_child(flee_seq)

    # 2. 运送
    transport_seq = py_trees.composites.Sequence(name="Transport", memory=True)
    transport_seq.add_child(CarryingResources(name="Has_Resources"))
    transport_seq.add_child(MoveToBase(name="To_Base"))
    transport_seq.add_child(DepositResources(name="Deposit"))
    root.add_child(transport_seq)

    # 3. 采集
    gather_seq = py_trees.composites.Sequence(name="Gather", memory=True)
    gather_seq.add_child(NeedResources(name="Need_Res"))
    gather_seq.add_child(MoveToResourceNode(name="To_Node"))
    gather_seq.add_child(GatherResources(name="Gather"))
    root.add_child(gather_seq)

    # 4. 制作 (辅助)
    craft_seq = py_trees.composites.Sequence(name="Craft", memory=True)
    craft_seq.add_child(HasCraftOrder(name="Has_Craft"))
    craft_seq.add_child(MoveToBuildSite(name="To_Bench"))
    craft_seq.add_child(AtWorkbench(name="At_Bench"))
    craft_seq.add_child(CraftWeapon(name="Craft"))
    root.add_child(craft_seq)

    # 5. 拾取武器
    pickup_seq = py_trees.composites.Sequence(name="Pickup", memory=True)
    pickup_seq.add_child(NoWeaponEquipped(name="No_Weapon"))
    pickup_seq.add_child(WeaponOnGround(name="Weapon_Near"))
    pickup_seq.add_child(MoveToWeapon(name="To_Weapon"))
    pickup_seq.add_child(EquipWeapon(name="Equip"))
    root.add_child(pickup_seq)

    # 6. 漫步
    root.add_child(Wander(name="Wander"))

    return root


def create_builder_behavior_tree(unit_name: str = "Builder") -> py_trees.behaviour.Behaviour:
    """创建建造者行为树.

    优先级:
    1. 逃跑
    2. 建造 (有建造订单)
    3. 制作 (有制作订单)
    4. 运送资源
    5. 采集 (空闲时辅助)
    6. 拾取武器
    7. 漫步
    """
    root = py_trees.composites.Selector(name=f"{unit_name}_Builder", memory=False)

    # 1. 逃跑
    flee_seq = py_trees.composites.Sequence(name="Flee", memory=True)
    flee_seq.add_child(HPCheck(name="HP_Low"))
    flee_seq.add_child(FleeToBase(name="Flee"))
    root.add_child(flee_seq)

    # 2. 建造
    build_seq = py_trees.composites.Sequence(name="Build", memory=True)
    build_seq.add_child(HasBuildOrder(name="Has_Build"))
    build_seq.add_child(MoveToBuildSite(name="To_Site"))
    build_seq.add_child(Build(name="Build"))
    root.add_child(build_seq)

    # 3. 制作
    craft_seq = py_trees.composites.Sequence(name="Craft", memory=True)
    craft_seq.add_child(HasCraftOrder(name="Has_Craft"))
    craft_seq.add_child(MoveToBuildSite(name="To_Bench"))
    craft_seq.add_child(AtWorkbench(name="At_Bench"))
    craft_seq.add_child(CraftWeapon(name="Craft"))
    root.add_child(craft_seq)

    # 4. 运送
    transport_seq = py_trees.composites.Sequence(name="Transport", memory=True)
    transport_seq.add_child(CarryingResources(name="Has_Res"))
    transport_seq.add_child(MoveToBase(name="To_Base"))
    transport_seq.add_child(DepositResources(name="Deposit"))
    root.add_child(transport_seq)

    # 5. 辅助采集
    gather_seq = py_trees.composites.Sequence(name="Gather", memory=True)
    gather_seq.add_child(NeedResources(name="Need_Res"))
    gather_seq.add_child(MoveToResourceNode(name="To_Node"))
    gather_seq.add_child(GatherResources(name="Gather"))
    root.add_child(gather_seq)

    # 6. 拾取武器
    pickup_seq = py_trees.composites.Sequence(name="Pickup", memory=True)
    pickup_seq.add_child(NoWeaponEquipped(name="No_Weapon"))
    pickup_seq.add_child(WeaponOnGround(name="Weapon_Near"))
    pickup_seq.add_child(MoveToWeapon(name="To_Weapon"))
    pickup_seq.add_child(EquipWeapon(name="Equip"))
    root.add_child(pickup_seq)

    # 7. 漫步
    root.add_child(Wander(name="Wander"))

    return root


def create_soldier_behavior_tree(unit_name: str = "Soldier") -> py_trees.behaviour.Behaviour:
    """创建战士行为树.

    优先级:
    1. 逃跑 (HP极低)
    2. 攻击 (敌人在攻击范围)
    3. 追击 (敌人可见)
    4. 巡逻 (向敌方移动)
    5. 拾取武器
    6. 运送资源 (如果携带)
    7. 漫步
    """
    root = py_trees.composites.Selector(name=f"{unit_name}_Soldier", memory=False)

    # 1. 逃跑 (更低的阈值)
    flee_seq = py_trees.composites.Sequence(name="Flee", memory=True)
    flee_seq.add_child(HPCheck(name="HP_Critical"))
    flee_seq.add_child(FleeToBase(name="Flee"))
    root.add_child(flee_seq)

    # 2. 攻击
    attack_seq = py_trees.composites.Sequence(name="Attack", memory=True)
    attack_seq.add_child(EnemyInAttackRange(name="Enemy_In_Range"))
    attack_seq.add_child(ExecuteAttack(name="Attack"))
    root.add_child(attack_seq)

    # 3. 追击
    chase_seq = py_trees.composites.Sequence(name="Chase", memory=True)
    chase_seq.add_child(EnemyInSight(name="Enemy_Visible"))
    chase_seq.add_child(ChaseEnemy(name="Chase"))
    root.add_child(chase_seq)

    # 4. 巡逻
    root.add_child(Patrol(name="Patrol"))

    # 5. 拾取武器
    pickup_seq = py_trees.composites.Sequence(name="Pickup", memory=True)
    pickup_seq.add_child(NoWeaponEquipped(name="No_Weapon"))
    pickup_seq.add_child(WeaponOnGround(name="Weapon_Near"))
    pickup_seq.add_child(MoveToWeapon(name="To_Weapon"))
    pickup_seq.add_child(EquipWeapon(name="Equip"))
    root.add_child(pickup_seq)

    # 6. 运送 (如果有资源)
    transport_seq = py_trees.composites.Sequence(name="Transport", memory=True)
    transport_seq.add_child(CarryingResources(name="Has_Res"))
    transport_seq.add_child(MoveToBase(name="To_Base"))
    transport_seq.add_child(DepositResources(name="Deposit"))
    root.add_child(transport_seq)

    # 7. 漫步
    root.add_child(Wander(name="Wander"))

    return root


def create_scout_behavior_tree(unit_name: str = "Scout") -> py_trees.behaviour.Behaviour:
    """创建侦察行为树.

    优先级:
    1. 逃跑 (HP低)
    2. 侦察 (向敌方区域移动并返回)
    3. 攻击 (敌人在攻击范围且无更好选择)
    4. 拾取武器
    5. 巡逻
    """
    root = py_trees.composites.Selector(name=f"{unit_name}_Scout", memory=False)

    # 1. 逃跑
    flee_seq = py_trees.composites.Sequence(name="Flee", memory=True)
    flee_seq.add_child(HPCheck(name="HP_Low"))
    flee_seq.add_child(FleeToBase(name="Flee"))
    root.add_child(flee_seq)

    # 2. 侦察
    root.add_child(ScoutArea(name="Scout"))

    # 3. 攻击 (仅近距离)
    attack_seq = py_trees.composites.Sequence(name="Attack", memory=True)
    attack_seq.add_child(EnemyInAttackRange(name="Enemy_In_Range"))
    attack_seq.add_child(ExecuteAttack(name="Attack"))
    root.add_child(attack_seq)

    # 4. 拾取武器
    pickup_seq = py_trees.composites.Sequence(name="Pickup", memory=True)
    pickup_seq.add_child(NoWeaponEquipped(name="No_Weapon"))
    pickup_seq.add_child(WeaponOnGround(name="Weapon_Near"))
    pickup_seq.add_child(MoveToWeapon(name="To_Weapon"))
    pickup_seq.add_child(EquipWeapon(name="Equip"))
    root.add_child(pickup_seq)

    # 5. 巡逻
    root.add_child(Patrol(name="Patrol"))

    return root


def create_unit_behavior_tree(
    unit_name: str = "UnitBT",
) -> py_trees.behaviour.Behaviour:
    """创建默认（空闲）单位行为树.

    9层优先级选择器，保留原有逻辑。
    """
    root = py_trees.composites.Selector(
        name=f"{unit_name}_Root",
        memory=False,
    )

    # ── 优先级 1: 逃跑 ──
    flee_sequence = py_trees.composites.Sequence(name="Flee_Sequence", memory=True)
    flee_sequence.add_child(HPCheck(name="HP_Check"))
    flee_sequence.add_child(FleeToBase(name="Flee"))
    root.add_child(flee_sequence)

    # ── 优先级 2: 攻击 ──
    attack_sequence = py_trees.composites.Sequence(name="Attack_Sequence", memory=True)
    attack_sequence.add_child(EnemyInAttackRange(name="Enemy_In_AtkRange"))
    attack_sequence.add_child(ExecuteAttack(name="Attack"))
    root.add_child(attack_sequence)

    # ── 优先级 3: 追击 ──
    chase_sequence = py_trees.composites.Sequence(name="Chase_Sequence", memory=True)
    chase_sequence.add_child(EnemyInSight(name="Enemy_In_Sight"))
    chase_sequence.add_child(ChaseEnemy(name="Chase"))
    root.add_child(chase_sequence)

    # ── 优先级 4: 建造 ──
    build_sequence = py_trees.composites.Sequence(name="Build_Sequence", memory=True)
    build_sequence.add_child(HasBuildOrder(name="Has_BuildOrder"))
    build_sequence.add_child(MoveToBuildSite(name="Move_To_BuildSite"))
    build_sequence.add_child(Build(name="Build"))
    root.add_child(build_sequence)

    # ── 优先级 5: 制作 ──
    craft_sequence = py_trees.composites.Sequence(name="Craft_Sequence", memory=True)
    craft_sequence.add_child(HasCraftOrder(name="Has_CraftOrder"))
    craft_sequence.add_child(MoveToBuildSite(name="Move_To_Workbench"))
    craft_sequence.add_child(AtWorkbench(name="At_Workbench"))
    craft_sequence.add_child(CraftWeapon(name="Craft"))
    root.add_child(craft_sequence)

    # ── 优先级 6: 运送资源 ──
    transport_sequence = py_trees.composites.Sequence(name="Transport_Sequence", memory=True)
    transport_sequence.add_child(CarryingResources(name="Has_Resources"))
    transport_sequence.add_child(MoveToBase(name="Move_To_Base"))
    transport_sequence.add_child(DepositResources(name="Deposit"))
    root.add_child(transport_sequence)

    # ── 优先级 7: 采集 ──
    gather_sequence = py_trees.composites.Sequence(name="Gather_Sequence", memory=True)
    gather_sequence.add_child(NeedResources(name="Need_Resources"))
    gather_sequence.add_child(MoveToResourceNode(name="Move_To_Node"))
    gather_sequence.add_child(GatherResources(name="Gather"))
    root.add_child(gather_sequence)

    # ── 优先级 8: 拾取武器 ──
    pickup_sequence = py_trees.composites.Sequence(name="Pickup_Sequence", memory=True)
    pickup_sequence.add_child(NoWeaponEquipped(name="No_Weapon"))
    pickup_sequence.add_child(WeaponOnGround(name="Weapon_Nearby"))
    pickup_sequence.add_child(MoveToWeapon(name="Move_To_Weapon"))
    pickup_sequence.add_child(EquipWeapon(name="Pickup"))
    root.add_child(pickup_sequence)

    # ── 优先级 9: 探索 ──
    explore_sequence = py_trees.composites.Sequence(name="Explore_Sequence", memory=True)
    explore_sequence.add_child(MoveTowardEnemy(name="Move_To_EnemySide"))
    explore_sequence.add_child(Wander(name="Wander"))
    root.add_child(explore_sequence)

    return root


def create_behavior_tree_for_role(role: str, unit_id: int, unit_name: str = "Unit") -> py_trees.behaviour.Behaviour:
    """根据角色创建对应行为树.

    Args:
        role: 角色名称 ("gatherer"|"builder"|"soldier"|"scout"|"idle")
        unit_id: 单位ID
        unit_name: 单位名称

    Returns:
        行为树根节点
    """
    name_prefix = f"{unit_name}_{unit_id}"
    if role == "gatherer":
        return create_gatherer_behavior_tree(name_prefix)
    elif role == "builder":
        return create_builder_behavior_tree(name_prefix)
    elif role == "soldier":
        return create_soldier_behavior_tree(name_prefix)
    elif role == "scout":
        return create_scout_behavior_tree(name_prefix)
    else:
        return create_unit_behavior_tree(name_prefix)


def create_behavior_tree_for_unit(
    unit_id: int,
    unit_name: str = "Unit",
) -> py_trees.behaviour.Behaviour:
    """为特定单位创建默认行为树（向后兼容）."""
    return create_unit_behavior_tree(f"{unit_name}_{unit_id}")
