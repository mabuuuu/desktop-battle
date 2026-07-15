"""Desktop Battle - 任务栏地面物理体.

将 Windows 任务栏顶部转换为 pymunk 物理地面线段。
"""

from __future__ import annotations

import pymunk

from src.desktop.coord import screen_to_physics
from src.desktop.taskbar import Rect, get_taskbar_rect
from src.physics.body_factory import create_terrain_segment


def create_taskbar_ground(
    screen_height: int,
    friction: float = 0.8,
    elasticity: float = 0.1,
) -> tuple[pymunk.Body, pymunk.Segment] | None:
    """创建任务栏地面物理体.

    Args:
        screen_height: 屏幕高度 (px)
        friction: 地面摩擦
        elasticity: 地面弹性

    Returns:
        (body, shape) 或 None (检测不到任务栏时)
    """
    rect = get_taskbar_rect()
    if rect is None:
        return None

    p1 = screen_to_physics(float(rect.left), float(rect.top), screen_height)
    p2 = screen_to_physics(float(rect.right), float(rect.top), screen_height)

    return create_terrain_segment(
        x1=p1[0],
        y1=p1[1],
        x2=p2[0],
        y2=p2[1],
        friction=friction,
        elasticity=elasticity,
        radius=3.0,
    )


def get_taskbar_ground_y_physics(rect: Rect, screen_height: int) -> float:
    """获取任务栏顶部在 pymunk 坐标系中的 Y 值."""
    _, py = screen_to_physics(0.0, float(rect.top), screen_height)
    return py
