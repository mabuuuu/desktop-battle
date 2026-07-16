"""Desktop Battle - 视野感知系统.

每个单位有独立的信息收集范围:
- 前方视野: 朝向方向一定距离内是可见范围（扇形）
- 身后感知: 身后一定范围是可感知范围（较小半径圆形）
- 只有在感知范围内的事件才能触发行为

用于:
- 求援时，被求救的人看到求援者才会上前询问
- 战斗中，只有看到敌人才能追击
- 事件传播限制在感知范围内
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.unit import Unit
    from src.core.world import World


@dataclass
class PerceptionConfig:
    """感知配置."""

    forward_range: float = 100.0   # 前方视野距离(px)
    forward_angle: float = 120.0   # 前方视野角度(度, 总角度)
    backward_range: float = 40.0   # 身后感知距离(px)
    hearing_range: float = 60.0    # 听觉范围(px, 全方向)


class PerceptionSystem:
    """感知系统.

    提供静态方法判断单位能否感知到某个位置/事件。
    """

    @staticmethod
    def can_see(
        unit: Unit,
        target_x: float,
        target_y: float,
        world: World,
        config: PerceptionConfig | None = None,
    ) -> bool:
        """判断单位能否**看到**目标位置.

        前方视野为扇形，身后为小圆形。
        """
        if config is None:
            config = PerceptionConfig()

        sx, sy = unit.screen_position(world.screen_height)
        dx = target_x - sx
        dy = target_y - sy
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 1.0:
            return True  # 重合

        # 计算目标相对于单位的朝向角度
        target_angle = math.atan2(dy, dx)  # 弧度

        # 单位朝向角度 (右=0, 左=π)
        facing_angle = 0.0 if unit.facing_right else math.pi

        # 计算角度差
        angle_diff = abs(target_angle - facing_angle)
        # 归一化到 [0, π]
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff

        # 前方视野: 扇形
        half_fov = math.radians(config.forward_angle / 2)
        if angle_diff <= half_fov and dist <= config.forward_range:
            return True

        # 身后感知: 小圆形
        if dist <= config.backward_range:
            return True

        return False

    @staticmethod
    def can_perceive(
        unit: Unit,
        target_x: float,
        target_y: float,
        world: World,
        config: PerceptionConfig | None = None,
    ) -> bool:
        """判断单位能否**感知**到目标位置（看+听）.

        听觉是全方向的，范围较小。
        """
        if config is None:
            config = PerceptionConfig()

        # 先检查能否看到
        if PerceptionSystem.can_see(unit, target_x, target_y, world, config):
            return True

        # 检查听觉范围
        sx, sy = unit.screen_position(world.screen_height)
        dist = math.sqrt((target_x - sx) ** 2 + (target_y - sy) ** 2)
        return dist <= config.hearing_range

    @staticmethod
    def get_visible_enemies(unit: Unit, world: World, config: PerceptionConfig | None = None) -> list:
        """获取单位可见的敌方单位列表."""
        if config is None:
            config = PerceptionConfig()

        visible = []
        for other in world.units:
            if not other.alive or other.faction_name == unit.faction_name:
                continue
            ox, oy = other.screen_position(world.screen_height)
            if PerceptionSystem.can_see(unit, ox, oy, world, config):
                visible.append(other)
        return visible

    @staticmethod
    def get_perceived_events(unit: Unit, world: World, events: list, config: PerceptionConfig | None = None) -> list:
        """获取单位能感知到的事件列表."""
        if config is None:
            config = PerceptionConfig()

        perceived = []
        for event in events:
            ex = getattr(event, 'x', 0.0)
            ey = getattr(event, 'y', 0.0)
            if PerceptionSystem.can_perceive(unit, ex, ey, world, config):
                perceived.append(event)
        return perceived
