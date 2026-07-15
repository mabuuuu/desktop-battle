"""Desktop Battle - 建筑实体.

工具台、兵营的物理体与渲染。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pymunk

from src.desktop.coord import physics_to_screen
from src.physics.body_factory import create_building_body


@dataclass
class BuildingSpec:
    """建筑规格定义."""

    name: str
    building_type: str  # "workbench", "barracks"
    width: int
    height: int
    hp: int
    build_cost_wood: int
    build_cost_ore: int
    build_time: float  # 建造时间 (秒)
    level: int = 1


# 预定义建筑规格
BUILDING_SPECS: dict[tuple[str, int], BuildingSpec] = {
    ("workbench", 1): BuildingSpec(
        name="工具台 Lv1",
        building_type="workbench",
        width=30,
        height=20,
        hp=500,
        build_cost_wood=15,
        build_cost_ore=0,
        build_time=10.0,
        level=1,
    ),
    ("workbench", 2): BuildingSpec(
        name="工具台 Lv2",
        building_type="workbench",
        width=30,
        height=20,
        hp=600,
        build_cost_wood=15,
        build_cost_ore=10,
        build_time=15.0,
        level=2,
    ),
    ("workbench", 3): BuildingSpec(
        name="工具台 Lv3",
        building_type="workbench",
        width=30,
        height=20,
        hp=700,
        build_cost_wood=10,
        build_cost_ore=20,
        build_time=20.0,
        level=3,
    ),
    ("barracks", 1): BuildingSpec(
        name="兵营",
        building_type="barracks",
        width=40,
        height=30,
        hp=800,
        build_cost_wood=20,
        build_cost_ore=10,
        build_time=20.0,
        level=1,
    ),
}


@dataclass
class Building:
    """建筑实体."""

    building_id: int
    faction_name: str
    faction_color_hex: str
    building_type: str
    level: int = 1

    # ── 物理体 ──
    body: pymunk.Body | None = None
    shape: pymunk.Poly | None = None

    # ── 属性 ──
    hp: float = 500.0
    max_hp: float = 500.0
    width: int = 30
    height: int = 20

    # ── 生产队列 (仅兵营) ──
    production_queue: list[float] = field(default_factory=list)

    # ── 渲染缓存 ──
    _rgba_color: tuple[int, int, int, int] = field(default=(255, 68, 68, 255))

    def __post_init__(self) -> None:
        self._rgba_color = self._hex_to_rgba(self.faction_color_hex)
        # 从规格加载属性
        spec = self.get_spec()
        if spec is not None:
            self.width = spec.width
            self.height = spec.height
            self.hp = float(spec.hp)
            self.max_hp = float(spec.hp)

    def get_spec(self) -> BuildingSpec | None:
        """获取建筑规格."""
        return BUILDING_SPECS.get((self.building_type, self.level))

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
        """初始化建筑物理体 (Static)."""
        body, shape = create_building_body(
            x=phys_x,
            y=phys_y,
            width=self.width,
            height=self.height,
            friction=0.8,
            elasticity=0.05,
        )
        self.body = body
        self.shape = shape
        shape.data = self

    def screen_position(self, screen_height: int) -> tuple[float, float]:
        """获取左下角屏幕坐标."""
        if self.body is None:
            return (0.0, 0.0)
        return physics_to_screen(self.body.position.x, self.body.position.y, screen_height)

    def can_produce(self) -> bool:
        """检查是否可以加入生产队列."""
        max_queue = 5
        return len(self.production_queue) < max_queue

    def add_to_queue(self, time_remaining: float) -> bool:
        """加入生产队列."""
        if not self.can_produce():
            return False
        self.production_queue.append(time_remaining)
        return True

    def update_production(self, dt: float) -> list[bool]:
        """更新生产队列，返回已完成项.

        Returns:
            每个队列项是否完成的布尔列表
        """
        completed: list[bool] = []
        for i in range(len(self.production_queue)):
            self.production_queue[i] -= dt
            if self.production_queue[i] <= 0.0:
                completed.append(True)
            else:
                completed.append(False)

        # 清理已完成的
        self.production_queue = [
            t for t, c in zip(self.production_queue, completed) if not c
        ]
        return completed

    def take_damage(self, damage: float) -> float:
        """建筑受到伤害."""
        self.hp = max(0.0, self.hp - damage)
        return damage

    @property
    def alive(self) -> bool:
        return self.hp > 0.0

    def render(self, buffer: np.ndarray, screen_height: int) -> None:
        """渲染建筑."""
        from src.render.sprite import draw_building, draw_health_bar

        sx, sy = self.screen_position(screen_height)

        # 绘制建筑
        draw_building(
            buffer,
            sx,
            sy - self.height,
            self.width,
            self.height,
            self._rgba_color,
            self.building_type,
            self.level,
        )

        # 绘制血条
        draw_health_bar(
            buffer,
            sx,
            sy - self.height - 6,
            self.width,
            3,
            self.hp,
            self.max_hp,
            self._rgba_color,
            (40, 40, 40, 180),
        )

        # 兵营生产进度指示
        if self.production_queue:
            from src.render.sprite import draw_text
            queue_text = f"Q:{len(self.production_queue)}"
            draw_text(
                buffer,
                sx + self.width // 2 - 5,
                sy - self.height - 14,
                queue_text,
                (255, 255, 200, 200),
                8,
            )
