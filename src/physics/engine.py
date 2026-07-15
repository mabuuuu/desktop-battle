"""Desktop Battle - pymunk 物理引擎封装.

物理世界配置、碰撞类型定义、碰撞回调注册。
兼容 pymunk >= 7.0 (使用 on_collision API).
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Callable

import pymunk


class CollisionType(IntEnum):
    """碰撞类型 ID."""

    UNIT = 1
    BUILDING = 2
    TERRAIN = 3
    RESOURCE_NODE = 4
    PROJECTILE = 5
    SENSOR = 6
    DROPPED_WEAPON = 7


class PhysicsEngine:
    """pymunk Space 封装.

    管理物理世界、碰撞处理、物理步进。
    """

    def __init__(
        self,
        gravity: tuple[float, float] = (0.0, 900.0),
        damping: float = 0.9,
        collision_slop: float = 0.5,
        iterations: int = 10,
    ) -> None:
        """初始化物理引擎.

        Args:
            gravity: 重力向量 (pymunk坐标系, Y轴向上, 所以 (0, 900) = 向下)
            damping: 全局速度阻尼
            collision_slop: 碰撞穿透容差
            iterations: 约束求解迭代次数
        """
        self.space: pymunk.Space = pymunk.Space()
        self.space.gravity = gravity
        self.space.damping = damping
        self.space.collision_slop = collision_slop
        self.space.iterations = iterations

        # 碰撞类型常量
        self.CT: type[CollisionType] = CollisionType

    def add_collision_handler(
        self,
        type_a: int,
        type_b: int,
        begin: Callable[[pymunk.Arbiter, pymunk.Space, Any], None] | None = None,
        pre_solve: Callable[[pymunk.Arbiter, pymunk.Space, Any], None] | None = None,
        post_solve: Callable[[pymunk.Arbiter, pymunk.Space, Any], None] | None = None,
        separate: Callable[[pymunk.Arbiter, pymunk.Space, Any], None] | None = None,
        data: Any = None,
    ) -> None:
        """注册碰撞回调 (pymunk >= 7.0).

        Args:
            type_a: 碰撞类型A
            type_b: 碰撞类型B
            begin: 碰撞开始时回调 (arbiter, space, data)
            pre_solve: 碰撞求解前回调
            post_solve: 碰撞求解后回调
            separate: 碰撞分离时回调
            data: 传递给回调的任意数据
        """
        self.space.on_collision(
            collision_type_a=type_a,
            collision_type_b=type_b,
            begin=begin,
            pre_solve=pre_solve,
            post_solve=post_solve,
            separate=separate,
            data=data,
        )

    def add_body(self, body: pymunk.Body, *shapes: pymunk.Shape) -> None:
        """向物理空间添加物体和形状."""
        self.space.add(body, *shapes)

    def remove_body(self, body: pymunk.Body, *shapes: pymunk.Shape) -> None:
        """从物理空间移除物体和形状."""
        self.space.remove(body, *shapes)

    def step(self, dt: float) -> None:
        """执行物理步进."""
        self.space.step(dt)

    @property
    def damping(self) -> float:
        return self.space.damping

    @damping.setter
    def damping(self, value: float) -> None:
        self.space.damping = value

    @property
    def gravity(self) -> tuple[float, float]:
        return self.space.gravity

    @gravity.setter
    def gravity(self, value: tuple[float, float]) -> None:
        self.space.gravity = value
