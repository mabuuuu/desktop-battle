"""Desktop Battle - 行为树条件节点.

基于 py_trees.behaviour.Behaviour 实现状态检查条件。
所有条件节点: SUCCESS 表示条件满足，FAILURE 表示不满足。
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import py_trees

if TYPE_CHECKING:
    from src.entity.unit import Unit


def _get_unit_from_blackboard(blackboard: py_trees.blackboard.Blackboard) -> Unit | None:
    """从黑板获取 unit 引用."""
    try:
        return blackboard.get("unit")
    except (KeyError, AttributeError):
        return None


def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    """两点间距离."""
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


class HPCheck(py_trees.behaviour.Behaviour):
    """HP低于阈值条件.

    Blackboard:
        unit: Unit 引用
        hp_threshold: float (可选, 默认 200.0)
    """

    def __init__(self, name: str = "HP Below Threshold") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        unit = _get_unit_from_blackboard(self.attach_blackboard_client().blackboard)
        if unit is None or not unit.alive:
            return py_trees.common.Status.FAILURE
        threshold = self.attach_blackboard_client().blackboard.get("hp_threshold", 200.0)
        if unit.hp < threshold:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class EnemyInSight(py_trees.behaviour.Behaviour):
    """视野范围内检测到敌人.

    Blackboard:
        unit: Unit 引用
        world: World 引用 (需要提供所有单位列表)
    """

    def __init__(self, name: str = "Enemy In Sight") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = self.attach_blackboard_client().blackboard
        unit = _get_unit_from_blackboard(bb)
        world = bb.get("world")
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        for other in world.units:
            if not other.alive or other.faction_name == unit.faction_name:
                continue
            ox, oy = other.screen_position(world.screen_height)
            if _distance(sx, sy, ox, oy) < unit.perception_range:
                bb.set("nearest_enemy", other)
                bb.set("nearest_enemy_dist", _distance(sx, sy, ox, oy))
                return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class EnemyInAttackRange(py_trees.behaviour.Behaviour):
    """敌人在攻击范围内.

    Blackboard:
        unit: Unit 引用
        nearest_enemy: Unit (由 EnemyInSight 设置)
    """

    def __init__(self, name: str = "Enemy In Attack Range") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = self.attach_blackboard_client().blackboard
        unit = _get_unit_from_blackboard(bb)
        enemy = bb.get("nearest_enemy")
        world = bb.get("world")
        if unit is None or enemy is None or world is None:
            return py_trees.common.Status.FAILURE
        if not enemy.alive:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        ex, ey = enemy.screen_position(world.screen_height)
        attack_range = 20.0  # 默认徒手范围
        if unit.weapon is not None:
            try:
                attack_range = unit.weapon.attack_range  # type: ignore[union-attr]
            except AttributeError:
                pass

        if _distance(sx, sy, ex, ey) < attack_range:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class HasBuildOrder(py_trees.behaviour.Behaviour):
    """阵营有未分配的建造订单.

    Blackboard:
        unit: Unit 引用
        faction_bb: FactionBlackboard
    """

    def __init__(self, name: str = "Has Build Order") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = self.attach_blackboard_client().blackboard
        unit = _get_unit_from_blackboard(bb)
        faction_bb = bb.get("faction_bb")
        if unit is None or faction_bb is None:
            return py_trees.common.Status.FAILURE
        order = faction_bb.get_next_build_order(unit.unit_id)
        if order is not None:
            bb.set("current_build_order", order)
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class HasCraftOrder(py_trees.behaviour.Behaviour):
    """阵营有未分配的制作订单.

    Blackboard:
        unit: Unit 引用
        faction_bb: FactionBlackboard
    """

    def __init__(self, name: str = "Has Craft Order") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = self.attach_blackboard_client().blackboard
        unit = _get_unit_from_blackboard(bb)
        faction_bb = bb.get("faction_bb")
        if unit is None or faction_bb is None:
            return py_trees.common.Status.FAILURE
        order = faction_bb.get_next_craft_order(unit.unit_id)
        if order is not None:
            bb.set("current_craft_order", order)
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class AtWorkbench(py_trees.behaviour.Behaviour):
    """单位在工具台旁边.

    Blackboard:
        unit: Unit 引用
        current_craft_order: CraftOrder
        world: World
    """

    def __init__(self, name: str = "At Workbench") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = self.attach_blackboard_client().blackboard
        unit = _get_unit_from_blackboard(bb)
        world = bb.get("world")
        craft_order = bb.get("current_craft_order")
        if unit is None or world is None or craft_order is None:
            return py_trees.common.Status.FAILURE

        # 查找目标工具台
        for b in world.buildings:
            if b.building_id == craft_order.workbench_building_id:
                sx, sy = unit.screen_position(world.screen_height)
                bx, by = b.screen_position(world.screen_height)
                if _distance(sx, sy, bx, by) < 40.0:
                    return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class CarryingResources(py_trees.behaviour.Behaviour):
    """单位携带了资源.

    Blackboard:
        unit: Unit 引用
    """

    def __init__(self, name: str = "Carrying Resources") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        unit = _get_unit_from_blackboard(self.attach_blackboard_client().blackboard)
        if unit is None:
            return py_trees.common.Status.FAILURE
        if unit.total_carried > 0:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class NeedResources(py_trees.behaviour.Behaviour):
    """单位未满载，需要采集更多资源.

    Blackboard:
        unit: Unit 引用
    """

    def __init__(self, name: str = "Need Resources") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        unit = _get_unit_from_blackboard(self.attach_blackboard_client().blackboard)
        if unit is None:
            return py_trees.common.Status.FAILURE
        if not unit.carrying_full:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class NoWeaponEquipped(py_trees.behaviour.Behaviour):
    """单位未装备武器.

    Blackboard:
        unit: Unit 引用
    """

    def __init__(self, name: str = "No Weapon Equipped") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        unit = _get_unit_from_blackboard(self.attach_blackboard_client().blackboard)
        if unit is None:
            return py_trees.common.Status.FAILURE
        if unit.weapon is None:
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class WeaponOnGround(py_trees.behaviour.Behaviour):
    """地面上有可拾取的武器.

    Blackboard:
        unit: Unit 引用
        world: World
    """

    def __init__(self, name: str = "Weapon On Ground") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = self.attach_blackboard_client().blackboard
        unit = _get_unit_from_blackboard(bb)
        world = bb.get("world")
        if unit is None or world is None:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        nearest_dist = float("inf")
        nearest_weapon = None
        for w in world.weapons_on_ground:
            if w.expired:
                continue
            d = _distance(sx, sy, w.drop_x, w.drop_y)
            if d < nearest_dist and d < unit.perception_range * 0.5:
                nearest_dist = d
                nearest_weapon = w

        if nearest_weapon is not None:
            bb.set("nearest_weapon", nearest_weapon)
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class NoHigherPriorityTask(py_trees.behaviour.Behaviour):
    """无更高优先级任务 (始终 SUCCESS，用于序列末尾通配).

    在 Selector 中作为最后一个子节点使用时，前面的条件
    都已经失败，说明可以执行低优先级行为。
    """

    def __init__(self, name: str = "No Higher Priority Task") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        return py_trees.common.Status.SUCCESS
