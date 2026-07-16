"""Desktop Battle - 拟真系统.

模拟真人的行为逻辑:
- 求援: 战场劣势时派人回基地求援
- 犹豫: 前往战场途中发现后方有人从事生产，会犹豫后返回
- 思考: 避免所有小人同时做同一决策（随机延迟+概率）
- 信息传播: 只有在视野/感知范围内的事件才能被感知

与行为树联动: 通过事件总线传递信息，行为树节点订阅事件。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.unit import Unit
    from src.core.world import World


class EmotionState(str, Enum):
    """情绪状态（影响决策）."""

    CALM = "calm"          # 平静
    ALERT = "alert"        # 警觉
    FEARFUL = "fearful"    # 恐惧
    BRAVE = "brave"        # 勇敢
    HESITANT = "hesitant"  # 犹豫


@dataclass
class UnitMind:
    """单位心理状态.

    每个单位有一个独立的思维模型，影响行为决策。
    """

    unit_id: int
    emotion: EmotionState = EmotionState.CALM
    morale: float = 1.0           # 士气 0.0~1.0
    hesitation_timer: float = 0.0 # 犹豫倒计时(秒)
    hesitation_action: str = ""   # 犹豫后要执行的动作
    last_decision_time: float = 0.0  # 上次做决策的时间
    decision_cooldown: float = 0.0   # 决策冷却(避免频繁切换)
    noticed_events: list[str] = field(default_factory=list)  # 近期注意到的消息ID

    def can_decide(self, current_time: float) -> bool:
        """是否可以做决策（冷却期检查）."""
        return current_time - self.last_decision_time >= self.decision_cooldown

    def set_cooldown(self, current_time: float, cooldown: float) -> None:
        """设置决策冷却."""
        self.last_decision_time = current_time
        self.decision_cooldown = cooldown


class SimulationSystem:
    """拟真系统管理器.

    每帧更新所有单位的心理状态和事件传播。
    """

    def __init__(self, world: World) -> None:
        self._world = world
        self._minds: dict[int, UnitMind] = {}
        self._pending_requests: list[HelpRequest] = []

    def get_mind(self, unit_id: int) -> UnitMind:
        """获取或创建单位思维模型."""
        if unit_id not in self._minds:
            self._minds[unit_id] = UnitMind(unit_id=unit_id)
        return self._minds[unit_id]

    def update(self, dt: float) -> None:
        """每帧更新拟真逻辑."""
        current_time = self._world.elapsed_time

        for unit in self._world.units:
            if not unit.alive:
                continue

            mind = self.get_mind(unit.unit_id)
            self._update_morale(unit, mind)
            self._update_emotion(unit, mind, current_time)
            self._process_hesitation(unit, mind, dt)
            self._check_help_requests(unit, mind, current_time)

        # 清理过期的求援请求
        self._pending_requests = [
            r for r in self._pending_requests
            if current_time - r.created_time < 15.0  # 15秒后过期
        ]

    def _update_morale(self, unit: Unit, mind: UnitMind) -> None:
        """更新士气（基于HP比例和周围情况）."""
        hp_ratio = unit.hp / unit.max_hp
        # 士气向HP比例靠拢
        target_morale = hp_ratio
        # 如果附近有友军，士气加成
        from src.behavior.conditions import _get_global_blackboard, _bb_get
        bb = _get_global_blackboard()
        world = _bb_get(bb, "world")
        if world is not None:
            sx, sy = unit.screen_position(world.screen_height)
            nearby_allies = 0
            nearby_enemies = 0
            for other in world.units:
                if not other.alive or other.unit_id == unit.unit_id:
                    continue
                ox, oy = other.screen_position(world.screen_height)
                dist = math.sqrt((sx - ox) ** 2 + (sy - oy) ** 2)
                if dist < 80.0:
                    if other.faction_name == unit.faction_name:
                        nearby_allies += 1
                    else:
                        nearby_enemies += 1

            # 友军多→士气加成，敌军多→士气下降
            if nearby_allies > nearby_enemies:
                target_morale = min(1.0, hp_ratio + 0.2)
            elif nearby_enemies > nearby_allies + 1:
                target_morale = max(0.0, hp_ratio - 0.3)

        # 平滑过渡
        mind.morale += (target_morale - mind.morale) * 0.05

    def _update_emotion(self, unit: Unit, mind: UnitMind, current_time: float) -> None:
        """根据士气更新情绪."""
        if mind.hesitation_timer > 0:
            mind.emotion = EmotionState.HESITANT
        elif mind.morale < 0.2:
            mind.emotion = EmotionState.FEARFUL
        elif mind.morale < 0.4:
            mind.emotion = EmotionState.ALERT
        elif mind.morale > 0.8:
            mind.emotion = EmotionState.BRAVE
        else:
            mind.emotion = EmotionState.CALM

    def _process_hesitation(self, unit: Unit, mind: UnitMind, dt: float) -> None:
        """处理犹豫行为.

        前往战场途中，发现后方有5+人从事生产，会犹豫后返回。
        但只有一定概率会犹豫（避免所有人同时犹豫）。
        """
        if mind.hesitation_timer > 0:
            mind.hesitation_timer -= dt
            if mind.hesitation_timer <= 0:
                # 犹豫结束，执行决定的动作
                if mind.hesitation_action == "return_to_work":
                    from src.entity.unit import UnitRole, UnitState
                    # 切换为生产者
                    unit.role = UnitRole.GATHERER
                    unit.state = UnitState.IDLE
                    # 通知黑板
                    from src.behavior.conditions import _get_global_blackboard, _bb_get
                    bb = _get_global_blackboard()
                    faction_bb = _bb_get(bb, "faction_bb")
                    if faction_bb is not None:
                        faction_bb.assign_role(unit.unit_id, "gatherer")
                mind.hesitation_action = ""
            return

        # 检查是否应该犹豫：战士前往战场途中
        from src.entity.unit import UnitRole, UnitState
        if unit.role != UnitRole.SOLDIER:
            return
        if unit.state not in (UnitState.WALKING, UnitState.PATROLLING):
            return
        if not mind.can_decide(self._world.elapsed_time):
            return

        # 检查后方是否有5+人从事生产
        from src.behavior.conditions import _get_global_blackboard, _bb_get
        bb = _get_global_blackboard()
        world = _bb_get(bb, "world")
        if world is None:
            return

        sx, sy = unit.screen_position(world.screen_height)
        # "后方" = 远离敌方的方向
        if unit.faction_name == world.factions[0].name:
            behind_x_range = (0, sx)  # 红方后方在左边
        else:
            behind_x_range = (sx, world.screen_width)  # 蓝方后方在右边

        producing_count = 0
        for other in world.units:
            if not other.alive or other.faction_name != unit.faction_name:
                continue
            if other.unit_id == unit.unit_id:
                continue
            if other.role in (UnitRole.GATHERER, UnitRole.BUILDER):
                ox, _ = other.screen_position(world.screen_height)
                if behind_x_range[0] <= ox <= behind_x_range[1]:
                    producing_count += 1

        # 5+人从事生产时，有20%概率犹豫
        if producing_count >= 5 and random.random() < 0.20:
            mind.hesitation_timer = random.uniform(1.5, 3.0)  # 犹豫1.5~3秒
            mind.hesitation_action = "return_to_work"
            unit.state = UnitState.IDLE  # 停下思考
            mind.set_cooldown(self._world.elapsed_time, 30.0)  # 30秒内不再犹豫

    def _check_help_requests(self, unit: Unit, mind: UnitMind, current_time: float) -> None:
        """检查是否有求援请求需要响应.

        只有在视野/感知范围内看到求援者才会响应。
        """
        from src.entity.unit import UnitRole, UnitState

        for request in self._pending_requests:
            if request.responder_id is not None:
                continue  # 已有人响应
            if request.faction_name != unit.faction_name:
                continue
            if unit.role in (UnitRole.GATHERER, UnitRole.BUILDER) and mind.morale < 0.5:
                continue  # 士气低的生产者不会去

            # 检查是否在感知范围内
            from src.simulation.perception import PerceptionSystem
            if not PerceptionSystem.can_perceive(unit, request.requester_x, request.requester_y, self._world):
                continue

            # 概率响应（避免所有人同时响应）
            if random.random() < 0.4:
                request.responder_id = unit.unit_id
                # 根据角色决定：去战场还是回基地报信
                if unit.role == UnitRole.SOLDIER or mind.morale > 0.6:
                    # 前往战场
                    unit.state = UnitState.WALKING
                    unit.move_toward(request.requester_x)
                else:
                    # 回基地报信
                    unit.state = UnitState.FLEEING
                    faction = None
                    for f in self._world.factions:
                        if f.name == unit.faction_name:
                            faction = f
                            break
                    if faction is not None:
                        unit.move_toward(faction.spawn_x)
                break

    def request_help(self, unit: Unit) -> None:
        """发起求援请求."""
        from src.behavior.conditions import _get_global_blackboard, _bb_get
        bb = _get_global_blackboard()
        world = _bb_get(bb, "world")
        if world is None:
            return

        sx, sy = unit.screen_position(world.screen_height)
        request = HelpRequest(
            requester_id=unit.unit_id,
            faction_name=unit.faction_name,
            requester_x=sx,
            requester_y=sy,
            created_time=self._world.elapsed_time,
        )
        self._pending_requests.append(request)


@dataclass
class HelpRequest:
    """求援请求."""

    requester_id: int
    faction_name: str
    requester_x: float
    requester_y: float
    created_time: float
    responder_id: int | None = None  # 响应者ID
