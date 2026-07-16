"""Desktop Battle - 建筑组装系统.

建筑由材料零件逐步组装而成:
- 每个建筑有预定义的零件列表（形状+数量）
- 资源点产生对应形状的材料零件
- 建造者从资源点搬运材料到建造现场
- 逐步拼装，全部零件到位后建筑完成并激活

例如:
  兵营 = [屋顶斜线×2, 墙体竖线×3, 地面横线×1]
  工具台 = [桌面横线×1, 桌腿竖线×2]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.entity.unit import Unit
    from src.core.world import World


class MaterialShape(str, Enum):
    """材料形状类型."""

    HORIZONTAL_BEAM = "horizontal_beam"  # 横梁
    VERTICAL_BEAM = "vertical_beam"      # 竖梁
    DIAGONAL_BEAM = "diagonal_beam"      # 斜梁（左下到右上）
    DIAGONAL_BEAM_R = "diagonal_beam_r"  # 斜梁（右下到左上）
    PLANK = "plank"                      # 木板（短横线）


@dataclass
class MaterialPart:
    """材料零件定义."""

    shape: MaterialShape
    length: int = 5   # 长度(px)
    count: int = 1    # 需要数量
    color_hint: str = "wood"  # "wood" | "ore" — 决定从哪种资源点获取


@dataclass
class PlacedPart:
    """已放置的零件（在建筑上）."""

    shape: MaterialShape
    x: float  # 相对建筑左上角偏移X
    y: float  # 相对建筑左上角偏移Y
    length: int
    placed: bool = False  # 是否已放置


@dataclass
class BuildingAssembly:
    """建筑组装定义.

    定义一个建筑的零件清单和每个零件的放置位置。
    """

    building_type: str
    level: int
    total_parts: list[PlacedPart] = field(default_factory=list)
    placed_count: int = 0

    @property
    def is_complete(self) -> bool:
        """建筑是否组装完成."""
        return all(p.placed for p in self.total_parts)

    @property
    def completion_ratio(self) -> float:
        """完成比例 0.0~1.0."""
        if not self.total_parts:
            return 1.0
        return sum(1 for p in self.total_parts if p.placed) / len(self.total_parts)

    def place_next_part(self) -> PlacedPart | None:
        """放置下一个未放置的零件."""
        for part in self.total_parts:
            if not part.placed:
                part.placed = True
                self.placed_count += 1
                return part
        return None

    def get_next_needed_shape(self) -> MaterialShape | None:
        """获取下一个需要的零件形状."""
        for part in self.total_parts:
            if not part.placed:
                return part.shape
        return None


# ── 预定义建筑组装模板 ──

def get_workbench_assembly() -> BuildingAssembly:
    """工具台组装: 桌面横线 + 两条桌腿."""
    return BuildingAssembly(
        building_type="workbench",
        level=1,
        total_parts=[
            # 桌面（横梁）
            PlacedPart(shape=MaterialShape.HORIZONTAL_BEAM, x=0, y=0, length=15),
            # 左桌腿（竖梁）
            PlacedPart(shape=MaterialShape.VERTICAL_BEAM, x=2, y=2, length=8),
            # 右桌腿（竖梁）
            PlacedPart(shape=MaterialShape.VERTICAL_BEAM, x=11, y=2, length=8),
        ],
    )


def get_barracks_assembly() -> BuildingAssembly:
    """兵营组装: 三角屋顶(2斜梁) + 三面墙体(3竖梁) + 地面(1横梁)."""
    return BuildingAssembly(
        building_type="barracks",
        level=1,
        total_parts=[
            # 屋顶左斜梁
            PlacedPart(shape=MaterialShape.DIAGONAL_BEAM, x=0, y=0, length=12),
            # 屋顶右斜梁
            PlacedPart(shape=MaterialShape.DIAGONAL_BEAM_R, x=10, y=0, length=12),
            # 左墙竖梁
            PlacedPart(shape=MaterialShape.VERTICAL_BEAM, x=0, y=5, length=10),
            # 右墙竖梁
            PlacedPart(shape=MaterialShape.VERTICAL_BEAM, x=18, y=5, length=10),
            # 后墙中间竖梁
            PlacedPart(shape=MaterialShape.VERTICAL_BEAM, x=9, y=5, length=10),
            # 地面横梁
            PlacedPart(shape=MaterialShape.HORIZONTAL_BEAM, x=0, y=14, length=20),
        ],
    )


BUILDING_ASSEMBLIES: dict[tuple[str, int], callable] = {
    ("workbench", 1): get_workbench_assembly,
    ("barracks", 1): get_barracks_assembly,
}


def get_assembly(building_type: str, level: int) -> BuildingAssembly | None:
    """获取建筑组装模板."""
    factory = BUILDING_ASSEMBLIES.get((building_type, level))
    if factory is None:
        return None
    return factory()


# ── 材料零件渲染 ──

def draw_material_part(
    buffer: np.ndarray,
    x: float,
    y: float,
    part: PlacedPart,
    color: tuple[int, int, int, int],
    line_width: int = 1,
) -> None:
    """在缓冲上绘制一个材料零件."""
    from src.render.sprite import draw_line

    if part.shape == MaterialShape.HORIZONTAL_BEAM:
        draw_line(buffer, x + part.x, y + part.y, x + part.x + part.length, y + part.y, color, line_width)
    elif part.shape == MaterialShape.VERTICAL_BEAM:
        draw_line(buffer, x + part.x, y + part.y, x + part.x, y + part.y + part.length, color, line_width)
    elif part.shape == MaterialShape.DIAGONAL_BEAM:
        draw_line(buffer, x + part.x, y + part.y + part.length, x + part.x + part.length, y + part.y, color, line_width)
    elif part.shape == MaterialShape.DIAGONAL_BEAM_R:
        draw_line(buffer, x + part.x, y + part.y, x + part.x + part.length, y + part.y + part.length, color, line_width)
    elif part.shape == MaterialShape.PLANK:
        draw_line(buffer, x + part.x, y + part.y, x + part.x + part.length, y + part.y, color, line_width)


def draw_assembly_progress(
    buffer: np.ndarray,
    x: float,
    y: float,
    assembly: BuildingAssembly,
    color: tuple[int, int, int, int],
    ghost_color: tuple[int, int, int, int],
    line_width: int = 1,
) -> None:
    """绘制建筑组装进度（已放置的零件实色，未放置的半透明）."""
    for part in assembly.total_parts:
        c = color if part.placed else ghost_color
        draw_material_part(buffer, x, y, part, c, line_width)


# ── 搬运材料 ──

@dataclass
class CarriedMaterial:
    """单位搬运的材料."""

    shape: MaterialShape
    length: int
    color_hint: str = "wood"
