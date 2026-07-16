"""Desktop Battle - 阵营行为黑板.

存储阵营级别的策略信息: 集结点、威胁等级、建造/制作订单、兵种需求。
被行为树节点的 conditions 和 actions 读取和写入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.unit import Unit


@dataclass
class BuildOrder:
    """建造订单."""

    building_type: str  # "workbench" | "barracks"
    level: int
    phys_x: float
    phys_y: float
    assigned_unit_id: int | None = None
    site_id: int | None = None


@dataclass
class CraftOrder:
    """制作订单."""

    weapon_name: str  # "spear" | "sword" | "shield"
    workbench_building_id: int
    assigned_unit_id: int | None = None


@dataclass
class FactionBlackboard:
    """阵营级别的行为黑板.

    存储策略信息和全局状态，供行为树节点读取。
    """

    faction_name: str = ""

    # ── 策略 ──
    current_strategy: str = "expand"  # "expand" | "rush" | "defense" | "tech"

    # ── 集结 ──
    rally_point: tuple[float, float] = (0.0, 0.0)  # (screen_x, screen_y)

    # ── 威胁 ──
    threat_level: float = 0.0  # 0.0 ~ 1.0 (越高越危险)

    # ── 建造订单 ──
    build_orders: list[BuildOrder] = field(default_factory=list)

    # ── 制作订单 ──
    craft_orders: list[CraftOrder] = field(default_factory=list)

    # ── 兵种需求 ──
    gatherers_needed: int = 2
    builders_needed: int = 1
    soldiers_needed: int = 2
    scouts_needed: int = 0

    # ── 全局目标 ──
    enemy_base_x: float = 0.0  # 敌方基地 screen X

    # ── 单位任务分配 ──
    # unit_id -> task_role ("gatherer" | "builder" | "soldier" | "scout" | "idle")
    unit_roles: dict[int, str] = field(default_factory=dict)

    def assign_role(self, unit_id: int, role: str) -> None:
        """分配单位角色."""
        self.unit_roles[unit_id] = role

    def get_role(self, unit_id: int) -> str:
        """获取单位角色."""
        return self.unit_roles.get(unit_id, "idle")

    def get_idle_units(self, all_units: list[Unit]) -> list[Unit]:
        """获取未分配角色的存活单位."""
        idle: list[Unit] = []
        for u in all_units:
            if u.alive and self.get_role(u.unit_id) == "idle":
                idle.append(u)
        return idle

    def count_role(self, role: str) -> int:
        """统计某角色的单位数."""
        return sum(1 for r in self.unit_roles.values() if r == role)

    def auto_assign_roles(self, all_units: list[Unit]) -> None:
        """自动分配角色以满足需求（动态策略）.

        根据当前策略调整角色比例:
        - expand: 采集优先 (3采集:1建造:1战士)
        - rush: 战斗优先 (1采集:0建造:4战士)
        - defense: 平衡 (2采集:1建造:2战士)
        - tech: 建造优先 (2采集:2建造:1战士)
        """
        alive_units = [u for u in all_units if u.alive]
        # 清除已死亡单位的角色记录
        alive_ids = {u.unit_id for u in alive_units}
        for uid in list(self.unit_roles.keys()):
            if uid not in alive_ids:
                del self.unit_roles[uid]

        idle_units = [u for u in alive_units if self.get_role(u.unit_id) == "idle"]
        if not idle_units:
            return

        # 根据策略动态调整需求
        total = len(alive_units)
        if self.current_strategy == "rush":
            needed: list[tuple[str, int]] = [
                ("gatherer", max(1, total // 5)),
                ("builder", 0),
                ("soldier", total - max(1, total // 5)),
                ("scout", max(1, total // 8)),
            ]
        elif self.current_strategy == "defense":
            needed = [
                ("gatherer", max(2, total // 3)),
                ("builder", max(1, total // 5)),
                ("soldier", max(2, total // 3)),
                ("scout", max(1, total // 8)),
            ]
        elif self.current_strategy == "tech":
            needed = [
                ("gatherer", max(2, total // 3)),
                ("builder", max(2, total // 4)),
                ("soldier", max(1, total // 5)),
                ("scout", 0),
            ]
        else:  # expand (默认)
            needed = [
                ("gatherer", max(3, total // 2)),
                ("builder", max(1, total // 5)),
                ("soldier", max(1, total // 3)),
                ("scout", max(1, total // 10)),
            ]

        for role, need in needed:
            current = self.count_role(role)
            deficit = need - current
            while deficit > 0 and idle_units:
                unit = idle_units.pop(0)
                self.assign_role(unit.unit_id, role)
                # 同步更新unit的role字段
                from src.entity.unit import UnitRole
                role_map = {
                    "gatherer": UnitRole.GATHERER,
                    "builder": UnitRole.BUILDER,
                    "soldier": UnitRole.SOLDIER,
                    "scout": UnitRole.SCOUT,
                }
                unit.role = role_map.get(role, UnitRole.IDLE)
                deficit -= 1

    def add_build_order(self, building_type: str, level: int, phys_x: float, phys_y: float) -> None:
        """添加建造订单."""
        self.build_orders.append(BuildOrder(
            building_type=building_type,
            level=level,
            phys_x=phys_x,
            phys_y=phys_y,
        ))

    def add_craft_order(self, weapon_name: str, workbench_id: int) -> None:
        """添加制作订单."""
        self.craft_orders.append(CraftOrder(
            weapon_name=weapon_name,
            workbench_building_id=workbench_id,
        ))

    def get_next_build_order(self, unit_id: int) -> BuildOrder | None:
        """获取未分配建造者的订单."""
        for order in self.build_orders:
            if order.assigned_unit_id is None:
                order.assigned_unit_id = unit_id
                return order
        return None

    def get_next_craft_order(self, unit_id: int) -> CraftOrder | None:
        """获取未分配制作者的订单."""
        for order in self.craft_orders:
            if order.assigned_unit_id is None:
                order.assigned_unit_id = unit_id
                return order
        return None
