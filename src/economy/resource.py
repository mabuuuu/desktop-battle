"""Desktop Battle - 资源管理.

阵营资源仓库、采集逻辑、运送存入。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.faction import Faction
    from src.entity.unit import Unit


def gather_resource(unit: Unit, node_type: str, dt: float, gather_speed: float) -> int:
    """单位在采集点采集资源.

    Args:
        unit: 采集单位
        node_type: "wood" 或 "ore"
        dt: 时间步长
        gather_speed: 采集速度 (资源/秒)

    Returns:
        本次采集到的资源量
    """
    if unit.carrying_full:
        return 0

    amount = int(gather_speed * dt)
    capacity_left = unit.config.unit_carry_capacity - unit.total_carried
    amount = min(amount, capacity_left)

    if amount <= 0:
        return 0

    if node_type == "wood":
        unit.carrying_wood += amount
    else:
        unit.carrying_ore += amount

    return amount


def deposit_resources(unit: Unit, faction: Faction) -> tuple[int, int]:
    """单位将携带的资源存入阵营仓库.

    Returns:
        (存入木材, 存入矿石)
    """
    wood, ore = unit.clear_carry()
    faction.add_wood(wood)
    faction.add_ore(ore)
    return (wood, ore)
