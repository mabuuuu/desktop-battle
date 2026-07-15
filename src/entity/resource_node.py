"""Desktop Battle - 资源采集点实体.

阵营出生时自带的木材/矿石采集点。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pymunk

from src.desktop.coord import physics_to_screen
from src.physics.body_factory import create_resource_node_body


@dataclass
class ResourceNode:
    """资源采集点实体.

    无限输出，每秒产出 resource_output_rate 单位资源。
    """

    node_id: int
    faction_name: str
    resource_type: str  # "wood" | "ore"
    color_hex: str
    secondary_color_hex: str
    screen_height: int = 1080

    # ── 物理体 ──
    body: pymunk.Body | None = None
    shape: pymunk.Circle | None = None

    # ── 属性 ──
    output_rate: float = 5.0  # 资源/秒
    size: int = 20  # 视觉尺寸 px

    # ── 动画 ──
    glow_phase: float = 0.0

    def __post_init__(self) -> None:
        self._rgba_color: tuple[int, int, int, int] = self._hex_to_rgba(self.color_hex)
        self._rgba_secondary: tuple[int, int, int, int] = self._hex_to_rgba(
            self.secondary_color_hex
        )

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
        hex_str = hex_color.lstrip("#")
        return (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
            alpha,
        )

    def init_physics(self, phys_x: float, phys_y: float) -> None:
        """初始化物理体."""
        body, shape = create_resource_node_body(phys_x, phys_y, radius=8.0)
        self.body = body
        self.shape = shape
        shape.data = self

    def screen_position(self, screen_height: int) -> tuple[float, float]:
        """获取屏幕坐标."""
        if self.body is None:
            return (0.0, 0.0)
        return physics_to_screen(self.body.position.x, self.body.position.y, screen_height)

    def update(self, dt: float) -> None:
        """更新动画相位."""
        self.glow_phase += dt * 2.0

    def render(self, buffer: np.ndarray, screen_height: int) -> None:
        """渲染采集点."""
        from src.render.sprite import draw_circle, draw_line

        sx, sy = self.screen_position(screen_height)

        # 采集点: 圆底 + 竖线(树干/矿柱) + 顶部标记
        color = self._rgba_color
        if self.resource_type == "wood":
            # 木材: 小树形状 (竖线+顶部横线)
            draw_line(buffer, sx, sy, sx, sy - 8, color, 1)       # 树干
            draw_line(buffer, sx - 3, sy - 6, sx + 3, sy - 6, color, 1)  # 树冠1
            draw_line(buffer, sx - 2, sy - 8, sx + 2, sy - 8, color, 1)  # 树冠2
        else:
            # 矿石: 三角形堆
            draw_line(buffer, sx, sy - 8, sx - 3, sy, color, 1)
            draw_line(buffer, sx, sy - 8, sx + 3, sy, color, 1)
            draw_line(buffer, sx - 3, sy, sx + 3, sy, color, 1)
