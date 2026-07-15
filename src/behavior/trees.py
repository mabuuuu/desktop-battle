"""Desktop Battle - 行为树构建器.

为单位创建9层优先级选择器行为树:
1. 逃跑 (HP低→逃回基地)
2. 攻击 (敌人在攻击范围内→攻击)
3. 追击 (敌人在视野内→追击)
4. 建造 (有建造订单→移动建造点→建造)
5. 制作 (有制作订单→移动工具台→制作)
6. 运送 (携带资源→回基地→存入)
7. 采集 (未满载→移动采集点→采集)
8. 拾取 (武器在地上→移动到武器→拾取)
9. 探索 (随机漫步/向敌方移动)
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
    NeedResources,
    NoWeaponEquipped,
    WeaponOnGround,
)

if TYPE_CHECKING:
    pass


def create_unit_behavior_tree(
    unit_name: str = "UnitBT",
) -> py_trees.behaviour.Behaviour:
    """创建单位行为树.

    9层优先级:
    1. 逃跑 (HP < 200 → FleeToBase)
    2. 攻击 (EnemyInAttackRange → ExecuteAttack)
    3. 追击 (EnemyInSight → ChaseEnemy)
    4. 建造 (HasBuildOrder → MoveToBuildSite → Build)
    5. 制作 (HasCraftOrder → AtWorkbench → CraftWeapon)
    6. 运送 (CarryingResources → MoveToBase → DepositResources)
    7. 采集 (NeedResources → MoveToResourceNode → GatherResources)
    8. 拾取 (NoWeaponEquipped & WeaponOnGround → MoveToWeapon → EquipWeapon)
    9. 探索 (MoveTowardEnemy / Wander)

    使用 py_trees.composites.Selector (优先级选择器) 和
    py_trees.composites.Sequence (顺序节点)。

    Args:
        unit_name: 行为树名称 (通常使用单位ID作为标识)

    Returns:
        行为树根节点
    """
    root = py_trees.composites.Selector(
        name=f"{unit_name}_Root",
        memory=False,
    )

    # ── 优先级 1: 逃跑 ──
    flee_sequence = py_trees.composites.Sequence(
        name="Flee_Sequence",
        memory=True,
    )
    flee_sequence.add_child(HPCheck(name="HP_Check"))
    flee_sequence.add_child(FleeToBase(name="Flee"))
    root.add_child(flee_sequence)

    # ── 优先级 2: 攻击 ──
    attack_sequence = py_trees.composites.Sequence(
        name="Attack_Sequence",
        memory=True,
    )
    attack_sequence.add_child(EnemyInAttackRange(name="Enemy_In_AtkRange"))
    attack_sequence.add_child(ExecuteAttack(name="Attack"))
    root.add_child(attack_sequence)

    # ── 优先级 3: 追击 ──
    chase_sequence = py_trees.composites.Sequence(
        name="Chase_Sequence",
        memory=True,
    )
    chase_sequence.add_child(EnemyInSight(name="Enemy_In_Sight"))
    chase_sequence.add_child(ChaseEnemy(name="Chase"))
    root.add_child(chase_sequence)

    # ── 优先级 4: 建造 ──
    build_sequence = py_trees.composites.Sequence(
        name="Build_Sequence",
        memory=True,
    )
    build_sequence.add_child(HasBuildOrder(name="Has_BuildOrder"))
    build_sequence.add_child(MoveToBuildSite(name="Move_To_BuildSite"))
    build_sequence.add_child(Build(name="Build"))
    root.add_child(build_sequence)

    # ── 优先级 5: 制作 ──
    craft_sequence = py_trees.composites.Sequence(
        name="Craft_Sequence",
        memory=True,
    )
    craft_sequence.add_child(HasCraftOrder(name="Has_CraftOrder"))
    craft_sequence.add_child(MoveToBuildSite(name="Move_To_Workbench"))
    craft_sequence.add_child(AtWorkbench(name="At_Workbench"))
    craft_sequence.add_child(CraftWeapon(name="Craft"))
    root.add_child(craft_sequence)

    # ── 优先级 6: 运送资源 ──
    transport_sequence = py_trees.composites.Sequence(
        name="Transport_Sequence",
        memory=True,
    )
    transport_sequence.add_child(CarryingResources(name="Has_Resources"))
    transport_sequence.add_child(MoveToBase(name="Move_To_Base"))
    transport_sequence.add_child(DepositResources(name="Deposit"))
    root.add_child(transport_sequence)

    # ── 优先级 7: 采集 ──
    gather_sequence = py_trees.composites.Sequence(
        name="Gather_Sequence",
        memory=True,
    )
    gather_sequence.add_child(NeedResources(name="Need_Resources"))
    gather_sequence.add_child(MoveToResourceNode(name="Move_To_Node"))
    gather_sequence.add_child(GatherResources(name="Gather"))
    root.add_child(gather_sequence)

    # ── 优先级 8: 拾取武器 ──
    pickup_sequence = py_trees.composites.Sequence(
        name="Pickup_Sequence",
        memory=True,
    )
    pickup_sequence.add_child(NoWeaponEquipped(name="No_Weapon"))
    pickup_sequence.add_child(WeaponOnGround(name="Weapon_Nearby"))
    pickup_sequence.add_child(MoveToWeapon(name="Move_To_Weapon"))
    pickup_sequence.add_child(EquipWeapon(name="Pickup"))
    root.add_child(pickup_sequence)

    # ── 优先级 9: 探索 ──
    explore_sequence = py_trees.composites.Sequence(
        name="Explore_Sequence",
        memory=True,
    )
    explore_sequence.add_child(MoveTowardEnemy(name="Move_To_EnemySide"))
    explore_sequence.add_child(Wander(name="Wander"))
    root.add_child(explore_sequence)

    return root


def create_behavior_tree_for_unit(
    unit_id: int,
    unit_name: str = "Unit",
) -> py_trees.behaviour.Behaviour:
    """为特定单位创建行为树.

    Args:
        unit_id: 单位ID
        unit_name: 单位名称

    Returns:
        行为树根节点
    """
    return create_unit_behavior_tree(f"{unit_name}_{unit_id}")
