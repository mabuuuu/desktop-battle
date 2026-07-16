"""Desktop Battle - 行为树动作节点.

所有动作节点: RUNNING 表示执行中, SUCCESS 表示完成, FAILURE 表示失败。
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import py_trees

from src.entity.unit import UnitState

if TYPE_CHECKING:
    from src.core.world import World
    from src.entity.unit import Unit


def _get_unit_and_world(bb: py_trees.blackboard.Blackboard) -> tuple[Unit | None, World | None]:
    """从黑板获取 unit 和 world."""
    unit = _bb_safe_get(bb, "unit")
    world = _bb_safe_get(bb, "world")
    return unit, world


def _bb_safe_get(bb: py_trees.blackboard.Blackboard, key: str, default: object = None) -> object:
    """安全获取黑板值 (py_trees v2 Blackboard.get 不支持默认参数)."""
    try:
        return bb.get(key)
    except KeyError:
        return default


def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


class FleeToBase(py_trees.behaviour.Behaviour):
    """低血量时逃回基地.

    Blackboard:
        unit: Unit
        world: World
        base_x: float (可选, 默认使用 faction.spawn_x)
    """

    def __init__(self, name: str = "Flee To Base") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        # 找到本方阵营的出生点
        faction = _find_faction(unit.faction_name, world)
        if faction is None:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        target_x = faction.spawn_x
        dist = abs(sx - target_x)

        if dist < 30.0:
            unit.state = UnitState.IDLE
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.FLEEING
        unit.move_toward(target_x)
        return py_trees.common.Status.RUNNING


class ExecuteAttack(py_trees.behaviour.Behaviour):
    """执行攻击动作：对 nearest_enemy 造成伤害.

    Blackboard:
        unit: Unit
        world: World
        nearest_enemy: Unit
    """

    def __init__(self, name: str = "Execute Attack") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        enemy = _bb_safe_get(bb,"nearest_enemy")
        if unit is None or world is None or enemy is None:
            return py_trees.common.Status.FAILURE
        if not enemy.alive:
            unit.combat_target_id = None
            return py_trees.common.Status.SUCCESS

        from src.combat.attack import execute_melee_attack

        unit.state = UnitState.FIGHTING
        unit.combat_target_id = enemy.unit_id

        # 面向敌人方向
        sx, sy = unit.screen_position(world.screen_height)
        ex, ey = enemy.screen_position(world.screen_height)
        unit.facing_right = ex >= sx

        if unit.attack_cooldown <= 0.0:
            result = execute_melee_attack(unit, enemy, world)
            if result:
                unit.attack_cooldown = _get_attack_cooldown(unit)
            return py_trees.common.Status.RUNNING
        else:
            unit.attack_cooldown -= getattr(world, "elapsed_time", 0.016)
            return py_trees.common.Status.RUNNING


class ChaseEnemy(py_trees.behaviour.Behaviour):
    """追击敌人: 移动向敌人位置.

    Blackboard:
        unit: Unit
        world: World
        nearest_enemy: Unit
    """

    def __init__(self, name: str = "Chase Enemy") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        enemy = _bb_safe_get(bb,"nearest_enemy")
        if unit is None or world is None or enemy is None:
            return py_trees.common.Status.FAILURE
        if not enemy.alive:
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        ex, ey = enemy.screen_position(world.screen_height)
        unit.move_toward(ex)
        return py_trees.common.Status.RUNNING


class MoveTowardEnemy(py_trees.behaviour.Behaviour):
    """向敌方基地移动 (探索行为).

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Move Toward Enemy") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        faction_bb = _bb_safe_get(bb,"faction_bb")
        target_x = 0.0
        s_width = world.screen_width
        if unit.faction_name == world.factions[0].name:
            target_x = s_width * 0.8
        else:
            target_x = s_width * 0.2

        if faction_bb is not None:
            target_x = faction_bb.enemy_base_x if faction_bb.enemy_base_x != 0.0 else target_x

        sx, sy = unit.screen_position(world.screen_height)
        if abs(sx - target_x) < 100.0:
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        unit.move_toward(target_x)
        return py_trees.common.Status.RUNNING


class MoveToBuildSite(py_trees.behaviour.Behaviour):
    """移动到建造地点.

    Blackboard:
        unit: Unit
        world: World
        current_build_order: BuildOrder
    """

    def __init__(self, name: str = "Move To Build Site") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        build_order = _bb_safe_get(bb,"current_build_order")
        if unit is None or world is None or build_order is None:
            return py_trees.common.Status.FAILURE

        from src.desktop.coord import physics_to_screen
        tx, ty = physics_to_screen(build_order.phys_x, build_order.phys_y, world.screen_height)
        sx, sy = unit.screen_position(world.screen_height)

        if _distance(sx, sy, tx, ty) < 40.0:
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        unit.move_toward(tx)
        return py_trees.common.Status.RUNNING


class Build(py_trees.behaviour.Behaviour):
    """执行建造动作.

    Blackboard:
        unit: Unit
        world: World
        current_build_order: BuildOrder
    """

    def __init__(self, name: str = "Build") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        build_order = _bb_safe_get(bb,"current_build_order")
        if unit is None or world is None or build_order is None:
            return py_trees.common.Status.FAILURE

        from src.entity.building import BUILDING_SPECS
        spec = BUILDING_SPECS.get((build_order.building_type, build_order.level))
        if spec is None:
            return py_trees.common.Status.FAILURE

        unit.state = UnitState.BUILDING

        # 建造进度
        if not hasattr(unit, "build_progress"):
            unit.build_progress = 0.0
        unit.build_progress += 0.05  # 每 tick 造 5%

        if unit.build_progress >= 1.0:
            # 建造完成
            faction = _find_faction(unit.faction_name, world)
            if faction is not None:
                world.create_building(
                    faction, build_order.building_type, build_order.level,
                    build_order.phys_x, build_order.phys_y,
                )
                faction.buildings_built += 1
            unit.build_progress = 0.0
            # 从订单列表移除
            bb_orders = _bb_safe_get(bb,"faction_bb")
            if bb_orders is not None:
                bb_orders.build_orders = [
                    o for o in bb_orders.build_orders if o != build_order
                ]
            unit.state = UnitState.IDLE
            return py_trees.common.Status.SUCCESS

        return py_trees.common.Status.RUNNING


class CraftWeapon(py_trees.behaviour.Behaviour):
    """在工作台制作武器.

    Blackboard:
        unit: Unit
        world: World
        current_craft_order: CraftOrder
    """

    def __init__(self, name: str = "Craft Weapon") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        craft_order = _bb_safe_get(bb,"current_craft_order")
        if unit is None or world is None or craft_order is None:
            return py_trees.common.Status.FAILURE

        unit.state = UnitState.CRAFTING
        faction = _find_faction(unit.faction_name, world)
        if faction is None:
            return py_trees.common.Status.FAILURE

        from src.combat.weapon import can_craft_at_station, get_weapon_spec
        from src.economy.crafting import CraftingJob

        spec = get_weapon_spec(craft_order.weapon_name)
        bench_level = faction.get_workbench_highest_level()
        if not can_craft_at_station(craft_order.weapon_name, bench_level):
            return py_trees.common.Status.FAILURE
        if not faction.can_afford(spec.crafting_cost_wood, spec.crafting_cost_ore):
            return py_trees.common.Status.FAILURE

        # 开始制作
        job = world.crafting.start_craft(craft_order.weapon_name, faction, unit)
        if job is not None:
            # 等待制作完成
            if job.done:
                bb_orders = _bb_safe_get(bb,"faction_bb")
                if bb_orders is not None:
                    bb_orders.craft_orders = [
                        o for o in bb_orders.craft_orders if o != craft_order
                    ]
                unit.state = UnitState.IDLE
                return py_trees.common.Status.SUCCESS
            return py_trees.common.Status.RUNNING
        return py_trees.common.Status.FAILURE


class MoveToBase(py_trees.behaviour.Behaviour):
    """移动回基地 (运送资源或撤退).

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Move To Base") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        faction = _find_faction(unit.faction_name, world)
        if faction is None:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        target_x = faction.spawn_x
        target_y = faction.spawn_y

        if _distance(sx, sy, target_x, target_y) < 50.0:
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        unit.move_toward(target_x)
        return py_trees.common.Status.RUNNING


class DepositResources(py_trees.behaviour.Behaviour):
    """将携带资源存入阵营仓库.

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Deposit Resources") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        faction = _find_faction(unit.faction_name, world)
        if faction is None:
            return py_trees.common.Status.FAILURE

        from src.economy.resource import deposit_resources
        wood, ore = deposit_resources(unit, faction)
        unit.state = UnitState.IDLE
        return py_trees.common.Status.SUCCESS


class MoveToResourceNode(py_trees.behaviour.Behaviour):
    """移动到资源采集点.

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Move To Resource Node") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        node = _find_nearest_resource_node(unit, world)
        if node is None:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        nx, ny = node.screen_position(world.screen_height)

        if _distance(sx, sy, nx, ny) < 30.0:
            bb.set("target_resource_node", node)
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        unit.move_toward(nx)
        return py_trees.common.Status.RUNNING


class GatherResources(py_trees.behaviour.Behaviour):
    """在采集点采集资源.

    Blackboard:
        unit: Unit
        world: World
        target_resource_node: ResourceNode
    """

    def __init__(self, name: str = "Gather Resources") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        node = _bb_safe_get(bb,"target_resource_node")
        if unit is None or world is None or node is None:
            return py_trees.common.Status.FAILURE
        if unit.carrying_full:
            return py_trees.common.Status.SUCCESS

        from src.economy.resource import gather_resource
        faction_cfg = getattr(unit, "faction_cfg", None)
        gather_speed = 5.0
        if faction_cfg is not None:
            try:
                gather_speed = faction_cfg.gather_speed  # type: ignore[union-attr]
            except AttributeError:
                pass

        unit.state = UnitState.MINING
        gather_resource(unit, node.resource_type, 0.1, gather_speed)
        return py_trees.common.Status.RUNNING


class MoveToWeapon(py_trees.behaviour.Behaviour):
    """移动到地上的武器.

    Blackboard:
        unit: Unit
        world: World
        nearest_weapon: WeaponInstance
    """

    def __init__(self, name: str = "Move To Weapon") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        weapon = _bb_safe_get(bb,"nearest_weapon")
        if unit is None or world is None or weapon is None:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        if _distance(sx, sy, weapon.drop_x, weapon.drop_y) < 20.0:
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        unit.move_toward(weapon.drop_x)
        return py_trees.common.Status.RUNNING


class EquipWeapon(py_trees.behaviour.Behaviour):
    """拾取地上的武器.

    Blackboard:
        unit: Unit
        world: World
        nearest_weapon: WeaponInstance
    """

    def __init__(self, name: str = "Equip Weapon") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        weapon = _bb_safe_get(bb,"nearest_weapon")
        if unit is None or world is None or weapon is None:
            return py_trees.common.Status.FAILURE

        weapon.pickup(unit.unit_id)
        unit.equip_weapon(weapon)
        if weapon in world.weapons_on_ground:
            world.weapons_on_ground.remove(weapon)
        bb.set("nearest_weapon", None)
        return py_trees.common.Status.SUCCESS


class Wander(py_trees.behaviour.Behaviour):
    """随机漫步探索.

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Wander") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        wander_target = _bb_safe_get(bb,"wander_target_x")
        if wander_target is None:
            sx, sy = unit.screen_position(world.screen_height)
            wander_target = sx + random.uniform(-80, 80)
            wander_target = max(10.0, min(float(world.screen_width) - 10, wander_target))
            bb.set("wander_target_x", wander_target)

        sx, sy = unit.screen_position(world.screen_height)
        if abs(sx - wander_target) < 15.0:
            bb.set("wander_target_x", None)
            unit.state = UnitState.IDLE
            return py_trees.common.Status.SUCCESS

        unit.state = UnitState.WALKING
        unit.move_toward(wander_target)
        return py_trees.common.Status.RUNNING


class Patrol(py_trees.behaviour.Behaviour):
    """巡逻: 在己方区域和前线之间移动.

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Patrol") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        faction_bb = _bb_safe_get(bb, "faction_bb")
        sx, sy = unit.screen_position(world.screen_height)

        # 巡逻目标: 在基地和前线之间交替
        patrol_target = _bb_safe_get(bb, "patrol_target_x")
        patrol_phase = _bb_safe_get(bb, "patrol_phase")

        if patrol_target is None or patrol_phase is None:
            # 初始化: 先去前线
            if unit.faction_name == world.factions[0].name:
                patrol_target = world.screen_width * 0.6
            else:
                patrol_target = world.screen_width * 0.4
            patrol_phase = "front"
            bb.set("patrol_target_x", patrol_target)
            bb.set("patrol_phase", patrol_phase)

        if abs(sx - float(patrol_target)) < 30.0:
            # 到达目标，切换方向
            if patrol_phase == "front":
                # 回基地附近
                if faction_bb is not None:
                    patrol_target = faction_bb.rally_point[0] + random.uniform(-30, 30)
                else:
                    patrol_target = sx - 100 * (1 if sx > world.screen_width / 2 else -1)
                bb.set("patrol_phase", "base")
            else:
                # 去前线
                if unit.faction_name == world.factions[0].name:
                    patrol_target = world.screen_width * 0.6 + random.uniform(-30, 30)
                else:
                    patrol_target = world.screen_width * 0.4 + random.uniform(-30, 30)
                bb.set("patrol_phase", "front")
            bb.set("patrol_target_x", patrol_target)

        unit.state = UnitState.PATROLLING
        unit.move_toward(float(patrol_target))
        return py_trees.common.Status.RUNNING


class ScoutArea(py_trees.behaviour.Behaviour):
    """侦察: 向敌方区域移动，发现敌人后返回报告.

    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Scout") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        sx, sy = unit.screen_position(world.screen_height)
        scout_phase = _bb_safe_get(bb, "scout_phase")

        if scout_phase is None:
            scout_phase = "advance"
            bb.set("scout_phase", scout_phase)

        if scout_phase == "advance":
            # 向敌方区域移动
            if unit.faction_name == world.factions[0].name:
                target_x = world.screen_width * 0.75
            else:
                target_x = world.screen_width * 0.25

            # 检测到敌人 → 标记威胁并返回
            for other in world.units:
                if other.alive and other.faction_name != unit.faction_name:
                    ox, oy = other.screen_position(world.screen_height)
                    if _distance(sx, sy, ox, oy) < unit.perception_range:
                        # 发现敌人，设置威胁信息
                        faction_bb = _bb_safe_get(bb, "faction_bb")
                        if faction_bb is not None:
                            faction_bb.threat_level = min(1.0, faction_bb.threat_level + 0.1)
                            faction_bb.enemy_base_x = ox
                        bb.set("scout_phase", "retreat")
                        break

            if scout_phase == "advance":
                if abs(sx - target_x) < 50.0:
                    # 到达敌方区域，返回
                    bb.set("scout_phase", "retreat")
                else:
                    unit.state = UnitState.SCOUTING
                    unit.move_toward(target_x)
                    return py_trees.common.Status.RUNNING

        if scout_phase == "retreat":
            # 返回基地
            faction = _find_faction(unit.faction_name, world)
            if faction is None:
                return py_trees.common.Status.FAILURE

            if abs(sx - faction.spawn_x) < 40.0:
                bb.set("scout_phase", None)
                unit.state = UnitState.IDLE
                return py_trees.common.Status.SUCCESS

            unit.state = UnitState.SCOUTING
            unit.move_toward(faction.spawn_x)
            return py_trees.common.Status.RUNNING

        return py_trees.common.Status.RUNNING


# ── 辅助函数 ──

def _find_faction(name: str, world: World) -> object | None:
    """查找阵营."""
    for f in world.factions:
        if f.name == name:
            return f
    return None


def _find_nearest_resource_node(unit: Unit, world: World) -> object | None:
    """找到最近的本方资源采集点."""
    sx, sy = unit.screen_position(world.screen_height)
    nearest = None
    nearest_dist = float("inf")
    for node in world.resource_nodes:
        if node.faction_name != unit.faction_name:
            continue
        nx, ny = node.screen_position(world.screen_height)
        d = _distance(sx, sy, nx, ny)
        if d < nearest_dist:
            nearest_dist = d
            nearest = node
    return nearest


def _get_attack_cooldown(unit: Unit) -> float:
    """获取攻击冷却时间."""
    if unit.weapon is not None:
        try:
            return unit.weapon.attack_speed  # type: ignore[union-attr]
        except AttributeError:
            pass
    return 1.5  # 徒手冷却


class RequestHelp(py_trees.behaviour.Behaviour):
    """求援: 战场劣势时派人回基地求援.

    触发条件: 士气低 + 附近敌军多于友军
    行为: 发出求援事件，附近的友军可能响应
    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Request Help") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        # 发起求援
        simulation = getattr(world, 'simulation', None)
        if simulation is not None:
            simulation.request_help(unit)

        # 发布求援事件
        event_bus = getattr(world, 'event_bus', None)
        if event_bus is not None:
            sx, sy = unit.screen_position(world.screen_height)
            from src.simulation.events import GameEvent, EventType
            event_bus.publish(GameEvent(
                event_type=EventType.HELP_REQUEST,
                x=sx, y=sy,
                faction_name=unit.faction_name,
                source_unit_id=unit.unit_id,
                created_time=world.elapsed_time,
                ttl=15.0,
            ))

        # 求援后继续战斗
        return py_trees.common.Status.SUCCESS


class RespondToHelp(py_trees.behaviour.Behaviour):
    """响应求援: 检查感知范围内的求援事件.

    看到求援者后决定: 去战场支援 或 回基地报信
    Blackboard:
        unit: Unit
        world: World
    """

    def __init__(self, name: str = "Respond To Help") -> None:
        super().__init__(name)

    def update(self) -> py_trees.common.Status:
        bb = py_trees.blackboard.Blackboard()
        unit, world = _get_unit_and_world(bb)
        if unit is None or world is None or not unit.alive:
            return py_trees.common.Status.FAILURE

        event_bus = getattr(world, 'event_bus', None)
        if event_bus is None:
            return py_trees.common.Status.FAILURE

        from src.simulation.events import EventType
        help_events = event_bus.get_events_for_unit(
            unit, world, world.elapsed_time,
            event_types=[EventType.HELP_REQUEST],
        )

        if not help_events:
            return py_trees.common.Status.FAILURE

        # 找最近的求援事件
        sx, sy = unit.screen_position(world.screen_height)
        nearest_event = min(help_events, key=lambda e: _distance(sx, sy, e.x, e.y))

        # 根据角色和士气决定
        from src.entity.unit import UnitRole
        simulation = getattr(world, 'simulation', None)
        if simulation is not None:
            mind = simulation.get_mind(unit.unit_id)
            if unit.role == UnitRole.SOLDIER or mind.morale > 0.5:
                # 前往支援
                unit.state = UnitState.WALKING
                unit.move_toward(nearest_event.x)
            else:
                # 回基地报信
                faction = _find_faction(unit.faction_name, world)
                if faction is not None:
                    unit.state = UnitState.FLEEING
                    unit.move_toward(faction.spawn_x)

        return py_trees.common.Status.SUCCESS
