"""Desktop Battle - 事件总线.

用于拟真系统中的信息传播。事件有位置属性，
只有在感知范围内的单位才能收到事件通知。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.unit import Unit
    from src.core.world import World


class EventType(str, Enum):
    """事件类型."""

    HELP_REQUEST = "help_request"       # 求援
    ENEMY_SPOTTED = "enemy_spotted"     # 发现敌人
    UNDER_ATTACK = "under_attack"       # 遭受攻击
    BUILDING_COMPLETE = "building_complete"  # 建造完成
    RESOURCE_FOUND = "resource_found"   # 发现资源
    SCHISM_WARNING = "schism_warning"   # 分裂预警
    CARRY_MATERIAL = "carry_material"   # 搬运材料


@dataclass
class GameEvent:
    """游戏事件."""

    event_type: EventType
    x: float                         # 事件发生位置X
    y: float                         # 事件发生位置Y
    faction_name: str                # 相关阵营
    source_unit_id: int | None = None  # 来源单位ID
    data: dict = field(default_factory=dict)  # 附加数据
    created_time: float = 0.0        # 创建时间
    ttl: float = 10.0                # 事件存活时间(秒)
    event_id: str = ""               # 唯一标识

    def is_expired(self, current_time: float) -> bool:
        """事件是否已过期."""
        return current_time - self.created_time > self.ttl


class EventBus:
    """事件总线.

    管理事件的发布和订阅。事件带有位置属性，
    单位只能收到感知范围内的事件。
    """

    def __init__(self) -> None:
        self._events: list[GameEvent] = []
        self._next_id: int = 0

    def publish(self, event: GameEvent) -> None:
        """发布事件."""
        if not event.event_id:
            self._next_id += 1
            event.event_id = f"evt_{self._next_id}"
        self._events.append(event)

    def get_events_for_unit(
        self,
        unit: Unit,
        world: World,
        current_time: float,
        event_types: list[EventType] | None = None,
    ) -> list[GameEvent]:
        """获取单位能感知到的事件.

        Args:
            unit: 目标单位
            world: 游戏世界
            current_time: 当前时间
            event_types: 过滤事件类型（None=全部）
        """
        from src.simulation.perception import PerceptionSystem

        perceived = []
        for event in self._events:
            # 过期事件跳过
            if event.is_expired(current_time):
                continue
            # 类型过滤
            if event_types and event.event_type not in event_types:
                continue
            # 阵营过滤（只接收本方阵营事件）
            if event.faction_name != unit.faction_name:
                continue
            # 感知范围检查
            if PerceptionSystem.can_perceive(unit, event.x, event.y, world):
                perceived.append(event)

        return perceived

    def cleanup(self, current_time: float) -> None:
        """清理过期事件."""
        self._events = [e for e in self._events if not e.is_expired(current_time)]

    @property
    def event_count(self) -> int:
        """当前事件数."""
        return len(self._events)
