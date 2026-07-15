"""Desktop Battle - 兵营生产队列.

兵营持续生产基础战士单位，消耗阵营资源。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.config import GameConfig
    from src.entity.building import Building
    from src.entity.faction import Faction


def try_start_production(
    building: Building,
    faction: Faction,
    config: GameConfig,
) -> bool:
    """尝试在兵营中开始生产一个单位.

    Args:
        building: 兵营建筑
        faction: 所属阵营
        config: 游戏配置

    Returns:
        是否成功加入生产队列
    """
    if building.building_type != "barracks":
        return False

    cost_wood = config.barracks_production_cost_wood
    cost_ore = config.barracks_production_cost_ore

    if not faction.can_afford(cost_wood, cost_ore):
        return False

    if not building.can_produce():
        return False

    # 扣除资源
    if not faction.spend(cost_wood, cost_ore):
        return False

    # 加入生产队列
    interval = config.barracks_production_interval
    return building.add_to_queue(interval)


def process_barracks_production(
    building: Building,
    faction: Faction,
    dt: float,
    unit_counter: list[int],  # [next_id] mutable ref for ID generation
) -> list[int]:
    """处理兵营生产队列，返回新生产的单位ID列表.

    Args:
        building: 兵营建筑
        faction: 所属阵营
        dt: 时间步长
        unit_counter: 单位ID计数器 (list[0] 为当前值)

    Returns:
        新生产的单位ID列表
    """
    if building.building_type != "barracks":
        return []

    completed = building.update_production(dt)
    new_unit_ids: list[int] = []

    for is_done in completed:
        if is_done:
            # 生产完成，创建新单位
            unit_id = unit_counter[0]
            unit_counter[0] += 1
            new_unit_ids.append(unit_id)

    return new_unit_ids
