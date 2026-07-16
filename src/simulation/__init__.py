"""Desktop Battle - 拟真系统包.

包含:
- perception: 视野感知系统
- realism: 拟真行为(求援/犹豫/思考)
- events: 事件总线
- building_assembly: 建筑组装系统
"""

from src.simulation.perception import PerceptionSystem, PerceptionConfig
from src.simulation.realism import SimulationSystem, UnitMind, EmotionState, HelpRequest
from src.simulation.events import EventBus, GameEvent, EventType
from src.simulation.building_assembly import (
    BuildingAssembly,
    MaterialShape,
    MaterialPart,
    PlacedPart,
    CarriedMaterial,
    get_assembly,
    draw_assembly_progress,
)
from src.simulation.debug import DebugSystem, DebugState

__all__ = [
    "PerceptionSystem",
    "PerceptionConfig",
    "SimulationSystem",
    "UnitMind",
    "EmotionState",
    "HelpRequest",
    "EventBus",
    "GameEvent",
    "EventType",
    "BuildingAssembly",
    "MaterialShape",
    "MaterialPart",
    "PlacedPart",
    "CarriedMaterial",
    "get_assembly",
    "draw_assembly_progress",
    "DebugSystem",
    "DebugState",
]
