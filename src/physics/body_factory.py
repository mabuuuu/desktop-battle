"""Desktop Battle - 物理体创建工厂.

为不同实体类型创建 pymunk Body + Shape 组合。
"""

from __future__ import annotations

import pymunk

from src.physics.engine import CollisionType


def create_unit_body(
    x: float,
    y: float,
    mass: float = 1.0,
    radius: float = 4.0,
    friction: float = 0.6,
    elasticity: float = 0.1,
) -> tuple[pymunk.Body, pymunk.Circle]:
    """创建单位物理体 (Dynamic, Circle).

    Args:
        x, y: 初始位置 (pymunk 坐标, Y向上)
        mass: 质量
        radius: 圆半径
        friction: 摩擦系数
        elasticity: 弹性系数
    """
    moment = pymunk.moment_for_circle(mass, 0.0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (x, y)

    shape = pymunk.Circle(body, radius)
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = CollisionType.UNIT

    return body, shape


def create_building_body(
    x: float,
    y: float,
    width: int,
    height: int,
    friction: float = 0.8,
    elasticity: float = 0.05,
) -> tuple[pymunk.Body, pymunk.Poly]:
    """创建建筑物理体 (Static, Box).

    Args:
        x, y: 左下角位置 (pymunk 坐标, Y向上)
        width: 宽度
        height: 高度
        friction: 摩擦系数
        elasticity: 弹性系数
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (x, y)

    shape = pymunk.Poly.create_box(body, (width, height))
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = CollisionType.BUILDING

    return body, shape


def create_terrain_segment(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    friction: float = 0.8,
    elasticity: float = 0.1,
    radius: float = 2.0,
) -> tuple[pymunk.Body, pymunk.Segment]:
    """创建地形线段物理体 (Static, Segment).

    Args:
        x1, y1: 线段起点 (pymunk 坐标)
        x2, y2: 线段终点 (pymunk 坐标)
        friction: 摩擦系数
        elasticity: 弹性系数
        radius: 线段厚度
    """
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, (x1, y1), (x2, y2), radius)
    shape.friction = friction
    shape.elasticity = elasticity
    shape.collision_type = CollisionType.TERRAIN

    return body, shape


def create_resource_node_body(
    x: float,
    y: float,
    radius: float = 8.0,
) -> tuple[pymunk.Body, pymunk.Circle]:
    """创建资源节点物理体 (Static, Circle) — 用作感知区域."""
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (x, y)

    shape = pymunk.Circle(body, radius)
    shape.sensor = True  # 传感器，不产生物理碰撞
    shape.collision_type = CollisionType.RESOURCE_NODE

    return body, shape


def create_sensor_body(
    x: float,
    y: float,
    radius: float,
) -> tuple[pymunk.Body, pymunk.Circle]:
    """创建通用传感器物理体 (无物理碰撞)."""
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (x, y)

    shape = pymunk.Circle(body, radius)
    shape.sensor = True
    shape.collision_type = CollisionType.SENSOR

    return body, shape


def create_projectile_body(
    x: float,
    y: float,
    velocity: tuple[float, float],
    mass: float = 0.1,
    radius: float = 2.0,
) -> tuple[pymunk.Body, pymunk.Circle]:
    """创建投射物物理体 (Dynamic, Circle)."""
    moment = pymunk.moment_for_circle(mass, 0.0, radius)
    body = pymunk.Body(mass, moment)
    body.position = (x, y)
    body.velocity = velocity

    shape = pymunk.Circle(body, radius)
    shape.collision_type = CollisionType.PROJECTILE
    shape.elasticity = 0.3

    return body, shape


def create_dropped_weapon_body(
    x: float,
    y: float,
    radius: float = 6.0,
) -> tuple[pymunk.Body, pymunk.Circle]:
    """创建掉落武器物理体 (Static, Sensor)."""
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (x, y)

    shape = pymunk.Circle(body, radius)
    shape.sensor = True
    shape.collision_type = CollisionType.DROPPED_WEAPON

    return body, shape
