"""Desktop Battle - 阵营管理.

阵营资源仓库、单位列表、建筑列表。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.config import FactionConfig
    from src.entity.building import Building
    from src.entity.unit import Unit


@dataclass
class Faction:
    """游戏阵营.

    管理该阵营的所有资源、单位、建筑。
    """

    config: FactionConfig

    # ── 资源 ──
    wood: int = 0
    ore: int = 0

    # ── 实体列表 ──
    units: list[Unit] = field(default_factory=list)
    buildings: list[Building] = field(default_factory=list)

    # ── 出生点 ──
    spawn_x: float = 0.0
    spawn_y: float = 0.0  # screen Y

    # ── 统计 ──
    units_produced: int = 0
    units_lost: int = 0
    buildings_built: int = 0
    buildings_lost: int = 0

    # ── 策略 ──
    current_strategy: str = "expand"

    # ── 分裂机制 ──
    conflict_score: float = 0.0  # 矛盾值 0~100
    schism_cooldown: float = 0.0  # 分裂冷却计时(秒)
    is_rebel: bool = False  # 是否为叛军阵营
    parent_faction_name: str = ""  # 叛军的原阵营名

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def color_hex(self) -> str:
        return self.config.color_hex

    @property
    def secondary_hex(self) -> str:
        return self.config.secondary_color_hex

    @property
    def alive_units(self) -> list[Unit]:
        """获取存活单位列表."""
        return [u for u in self.units if u.alive]

    @property
    def dead_units(self) -> int:
        """阵亡单位数."""
        return sum(1 for u in self.units if not u.alive)

    @property
    def alive_count(self) -> int:
        """存活单位数."""
        return len(self.alive_units)

    def add_unit(self, unit: Unit) -> None:
        """添加单位到阵营."""
        self.units.append(unit)

    def remove_unit(self, unit: Unit) -> None:
        """从阵营移除单位."""
        if unit in self.units:
            self.units.remove(unit)

    def add_building(self, building: Building) -> None:
        """添加建筑."""
        self.buildings.append(building)

    def remove_building(self, building: Building) -> None:
        """移除建筑."""
        if building in self.buildings:
            self.buildings.remove(building)

    def add_wood(self, amount: int) -> None:
        """添加木材."""
        self.wood += amount

    def add_ore(self, amount: int) -> None:
        """添加矿石."""
        self.ore += amount

    def can_afford(self, wood: int = 0, ore: int = 0) -> bool:
        """检查是否有足够资源."""
        return self.wood >= wood and self.ore >= ore

    def spend(self, wood: int = 0, ore: int = 0) -> bool:
        """扣除资源，不足则返回 False."""
        if not self.can_afford(wood, ore):
            return False
        self.wood -= wood
        self.ore -= ore
        return True

    def get_buildings_by_type(self, building_type: str) -> list[Building]:
        """获取指定类型的建筑列表."""
        return [b for b in self.buildings if b.building_type == building_type]

    def get_barracks_count(self) -> int:
        """获取兵营数量."""
        return len(self.get_buildings_by_type("barracks"))

    def get_workbench_highest_level(self) -> int:
        """获取最高工具台等级."""
        benches = self.get_buildings_by_type("workbench")
        if not benches:
            return 0
        return max(b.level for b in benches)
