"""Desktop Battle - 攀爬物理系统.

管理单位沿窗口边界攀爬的物理逻辑:
- 检测单位是否靠近垂直的窗口边缘
- 切换到攀爬模式 (KINEMATIC body_type)
- 沿墙壁上升/下降移动
- 到达顶部时切回 DYNAMIC 模式
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pymunk

from src.entity.unit import UnitState

if TYPE_CHECKING:
    from src.core.world import World
    from src.entity.unit import Unit


# 攀爬参数
CLIMB_CHECK_DISTANCE: float = 12.0  # 检测墙壁的距离阈值 (px)
CLIMB_SPEED: float = 40.0  # 攀爬速度 (px/s)
CLIMB_TOP_OFFSET: float = 10.0  # 到达顶部后额外上升距离


def check_and_start_climbing(unit: Unit, world: World) -> bool:
    """检测单位是否靠近墙壁，如果是则开始攀爬.

    Args:
        unit: 单位
        world: 世界引用

    Returns:
        是否开始攀爬
    """
    if unit.body is None or not unit.alive:
        return False
    if unit.state == UnitState.CLIMBING:
        return True
    if not unit.on_ground:
        return False

    # 获取单位物理位置
    px = unit.body.position.x
    py = unit.body.position.y

    # 检查附近的地形线段（窗口侧壁）
    for body, shapes in world._terrain_bodies:
        for shape in shapes:
            if not isinstance(shape, pymunk.Segment):
                continue

            a = shape.a  # 线段端点A (pymunk Vec2d)
            b = shape.b  # 线段端点B

            # 只处理垂直墙壁 (左右两侧)
            dx = abs(a.x - b.x)
            dy = abs(a.y - b.y)
            if dx > 5.0 or dy < 20.0:
                # 非垂直: 跳过水平平台
                continue

            # 墙壁的X坐标
            wall_x = a.x
            wall_min_y = min(a.y, b.y)
            wall_max_y = max(a.y, b.y)

            # 检查单位是否靠近墙壁
            if abs(px - wall_x) > CLIMB_CHECK_DISTANCE:
                continue
            # 单位必须在墙壁范围内
            if py < wall_min_y or py > wall_max_y:
                continue

            # 靠近墙壁 → 开始攀爬
            _start_climbing(unit, wall_x, wall_min_y, wall_max_y)
            return True

    return False


def _start_climbing(
    unit: Unit,
    wall_x: float,
    wall_min_y: float,
    wall_max_y: float,
) -> None:
    """开始攀爬模式:
    - 切换 body_type 为 KINEMATIC
    - 取消重力影响
    - 吸附到墙壁表面
    """
    if unit.body is None:
        return

    unit.body.body_type = pymunk.Body.KINEMATIC
    unit.body.velocity = (0.0, 0.0)

    # 吸附到墙壁
    direction = 1.0 if wall_x > unit.body.position.x else -1.0
    snap_x = wall_x - direction * CLIMB_CHECK_DISTANCE * 0.5
    unit.body.position = (snap_x, unit.body.position.y)

    unit.state = UnitState.CLIMBING
    unit.on_ground = False

    # 存储攀爬上下文 (利用私有属性)
    unit._climb_wall_x = wall_x  # type: ignore[attr-defined]
    unit._climb_wall_min_y: float = wall_min_y  # type: ignore[attr-defined]
    unit._climb_wall_max_y: float = wall_max_y  # type: ignore[attr-defined]
    unit._climb_direction: float = direction  # type: ignore[attr-defined]


def update_climbing(unit: Unit, dt: float, world: World) -> None:
    """更新攀爬状态.

    沿墙壁向上移动，到达顶部后切换到 Dynamic 模式并跳到窗口顶部。

    Args:
        unit: 单位
        dt: 时间步长
        world: 世界引用
    """
    if unit.state != UnitState.CLIMBING:
        return
    if unit.body is None or not unit.alive:
        return

    wall_x = getattr(unit, "_climb_wall_x", 0.0)
    wall_max_y = getattr(unit, "_climb_wall_max_y", 0.0)

    # 沿墙壁向上移动
    climb_speed = float(getattr(unit, "faction_cfg", None))
    try:
        if hasattr(unit.faction_cfg, "climb_speed"):
            climb_speed = float(unit.faction_cfg.climb_speed)  # type: ignore[union-attr]
        else:
            climb_speed = CLIMB_SPEED
    except (AttributeError, TypeError):
        climb_speed = CLIMB_SPEED

    new_y = unit.body.position.y + climb_speed * dt

    # 检测是否到达顶部
    if new_y >= wall_max_y - CLIMB_TOP_OFFSET:
        # 到达窗口顶部 → 结束攀爬，跳到平台
        _end_climbing_jump(unit, wall_x, wall_max_y, world)
        return

    # 沿墙壁更新位置
    direction = getattr(unit, "_climb_direction", 1.0)
    snap_x = wall_x - direction * CLIMB_CHECK_DISTANCE * 0.5
    unit.body.position = (snap_x, new_y)
    unit.body.velocity = (0.0, 0.0)


def _end_climbing_jump(
    unit: Unit,
    wall_x: float,
    wall_max_y: float,
    world: World,
) -> None:
    """攀爬结束: 切回 Dynamic 模式并跳到窗口顶部.

    Args:
        unit: 单位
        wall_x: 墙壁X坐标
        wall_max_y: 墙壁顶部Y坐标
        world: 世界引用 (未使用但保留接口)
    """
    if unit.body is None:
        return

    # 切回 Dynamic
    unit.body.body_type = pymunk.Body.DYNAMIC
    unit.body.velocity = (0.0, 0.0)

    # 放置到窗口顶部上方
    direction = getattr(unit, "_climb_direction", 1.0)
    landing_x = wall_x + direction * 20.0
    unit.body.position = (landing_x, wall_max_y + 10.0)

    # 轻微初始速度，模拟跳上
    unit.body.velocity = (direction * 30.0, 50.0)

    unit.state = UnitState.IDLE
    unit.on_ground = False

    # 清理攀爬状态
    if hasattr(unit, "_climb_wall_x"):
        delattr(unit, "_climb_wall_x")
    if hasattr(unit, "_climb_wall_min_y"):
        delattr(unit, "_climb_wall_min_y")
    if hasattr(unit, "_climb_wall_max_y"):
        delattr(unit, "_climb_wall_max_y")
    if hasattr(unit, "_climb_direction"):
        delattr(unit, "_climb_direction")


def is_near_wall(unit: Unit, world: World) -> bool:
    """检查单位是否靠近可攀爬的墙壁.

    Args:
        unit: 单位
        world: 世界引用

    Returns:
        是否靠近墙壁
    """
    if unit.body is None:
        return False

    px = unit.body.position.x
    py = unit.body.position.y

    for _body, shapes in world._terrain_bodies:
        for shape in shapes:
            if not isinstance(shape, pymunk.Segment):
                continue
            a = shape.a
            b = shape.b
            dx = abs(a.x - b.x)
            dy = abs(a.y - b.y)
            # 垂直墙壁
            if dx > 5.0 or dy < 20.0:
                continue
            wall_x = a.x
            wall_min_y = min(a.y, b.y)
            wall_max_y = max(a.y, b.y)
            if abs(px - wall_x) < CLIMB_CHECK_DISTANCE and wall_min_y <= py <= wall_max_y:
                return True
    return False
