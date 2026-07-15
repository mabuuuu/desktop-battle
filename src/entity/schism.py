"""Desktop Battle - 阵营分裂管理器.

当一方全灭后，胜利方继续发展，人口超阈值时内部矛盾积累，
矛盾值超限时触发分裂，产生叛军阵营，开启新一轮战斗。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pymunk

from src.desktop.coord import physics_to_screen
from src.entity.faction import Faction
from src.entity.resource_node import ResourceNode

if TYPE_CHECKING:
    from src.core.config import FactionConfig, GameConfig, SchismConfig
    from src.entity.unit import Unit
    from src.core.world import World


# 叛军阵营颜色映射: 原阵营主色 → 叛军主色/辅色
REBEL_COLORS: dict[str, tuple[str, str]] = {
    "#FF4444": ("#44FFEE", "#88FFCC"),  # 红方 → 青色叛军
    "#4488FF": ("#FFAA44", "#FFCC88"),  # 蓝方 → 橙色叛军
}


class SchismManager:
    """阵营分裂管理器.

    检测场上是否仅剩一方势力，如果是且人口超阈值，
    则积累矛盾值，触发争吵/小冲突，最终导致分裂。
    """

    def __init__(self, world: World) -> None:
        self.world: World = world
        self.config: SchismConfig = world.config.schism
        self._conflict_timer: float = 0.0  # 矛盾积累计时器
        self._argue_check_timer: float = 0.0  # 争吵检测计时器

    def update(self, dt: float) -> None:
        """每帧更新分裂机制."""
        if not self.config.enabled:
            return

        # 检查是否仅剩一方存活势力
        alive_factions = self._get_alive_factions()
        if len(alive_factions) != 1:
            # 多方势力存在，重置所有阵营矛盾
            for f in alive_factions:
                f.conflict_score = 0.0
            return

        faction = alive_factions[0]

        # 分裂冷却中
        if faction.schism_cooldown > 0:
            faction.schism_cooldown -= dt
            return

        alive_count = faction.alive_count

        # 人口未达阈值
        if alive_count < self.config.trigger_population:
            faction.conflict_score = 0.0
            return

        # 积累矛盾
        self._conflict_timer += dt
        if self._conflict_timer >= self.config.conflict_accumulate_interval:
            self._conflict_timer = 0.0
            pop_bonus = (alive_count - self.config.trigger_population) * self.config.conflict_population_bonus
            increment = self.config.conflict_base_rate + pop_bonus
            faction.conflict_score = min(
                self.config.conflict_max,
                faction.conflict_score + increment,
            )

        # 争吵和小冲突
        self._update_conflict_behaviors(faction, dt)

        # 检查是否触发分裂
        if faction.conflict_score >= self.config.schism_threshold:
            self._execute_schism(faction)

    def _get_alive_factions(self) -> list[Faction]:
        """获取存活的阵营（有至少1个存活单位）."""
        return [f for f in self.world.factions if f.alive_count > 0]

    def _update_conflict_behaviors(self, faction: Faction, dt: float) -> None:
        """更新争吵和小冲突行为."""
        from src.entity.unit import UnitState

        conflict = faction.conflict_score

        # 争吵检测 (矛盾值 >= 30)
        if conflict >= self.config.argue_threshold:
            self._argue_check_timer += dt
            if self._argue_check_timer >= 1.0:
                self._argue_check_timer = 0.0
                prob = conflict * self.config.argue_probability_per_second
                for unit in faction.alive_units:
                    if unit.state in (UnitState.IDLE, UnitState.WALKING):
                        if random.random() < prob:
                            self._trigger_argue(unit, faction)

        # 小冲突 (矛盾值 >= 60)
        if conflict >= self.config.skirmish_threshold:
            prob = (conflict - self.config.skirmish_threshold) * self.config.skirmish_probability_per_second
            for unit in faction.alive_units:
                if unit.state == UnitState.ARGUING:
                    if random.random() < prob * dt:
                        self._trigger_skirmish(unit, faction)

    def _trigger_argue(self, unit: Unit, faction: Faction) -> None:
        """触发单位争吵."""
        from src.entity.unit import UnitState

        duration = random.uniform(*self.config.argue_duration_range)
        unit.state = UnitState.ARGUING
        unit._argue_timer = duration  # type: ignore[attr-defined]

        # 找最近的同阵营单位作为争吵对象
        if unit.body is None:
            return
        sx, _ = unit.screen_position(self.world.screen_height)
        nearest: Unit | None = None
        nearest_dist = float("inf")
        for other in faction.alive_units:
            if other.unit_id == unit.unit_id or other.state == UnitState.ARGUING:
                continue
            ox, _ = other.screen_position(self.world.screen_height)
            d = abs(sx - ox)
            if d < nearest_dist and d < 50:
                nearest = other
                nearest_dist = d

        if nearest is not None:
            nearest.state = UnitState.ARGUING
            nearest._argue_timer = duration  # type: ignore[attr-defined]

    def _trigger_skirmish(self, unit: Unit, faction: Faction) -> None:
        """触发小冲突（击退，无伤害）."""
        if unit.body is None:
            return

        # 随机方向击退
        direction = random.choice([-1, 1])
        impulse = (direction * self.config.skirmish_knockback, self.config.skirmish_knockback * 0.2)
        unit.body.apply_impulse_at_local_point(impulse)

    def update_arguing_units(self, dt: float) -> None:
        """更新争吵中的单位计时器."""
        from src.entity.unit import UnitState

        for unit in self.world.units:
            if unit.state == UnitState.ARGUING and hasattr(unit, "_argue_timer"):
                unit._argue_timer -= dt  # type: ignore[attr-defined]
                if unit._argue_timer <= 0:  # type: ignore[attr-defined]
                    unit.state = UnitState.IDLE
                    del unit._argue_timer

    def _execute_schism(self, faction: Faction) -> None:
        """执行阵营分裂."""
        alive_units = faction.alive_units
        if len(alive_units) < 2:
            return

        # 计算分裂人数
        split_ratio = random.uniform(*self.config.split_ratio_range)
        split_count = max(2, int(len(alive_units) * split_ratio))
        split_count = min(split_count, len(alive_units) - 1)  # 至少留1人

        # 选择分裂单位（优先离阵营中心最远的）
        if faction.body is not None or len(alive_units) > 0:
            # 计算阵营中心
            positions = []
            for u in alive_units:
                if u.body is not None:
                    positions.append(u.body.position.x)
            if positions:
                center_x = sum(positions) / len(positions)
                # 按距中心距离降序排列
                alive_units_sorted = sorted(
                    alive_units,
                    key=lambda u: abs(u.body.position.x - center_x) if u.body is not None else 0,
                    reverse=True,
                )
            else:
                alive_units_sorted = list(alive_units)
        else:
            alive_units_sorted = list(alive_units)

        split_units = alive_units_sorted[:split_count]

        # 创建叛军阵营
        rebel_faction = self._create_rebel_faction(faction)

        # 转移单位
        for unit in split_units:
            unit.faction_name = rebel_faction.name
            unit.faction_color_hex = rebel_faction.color_hex
            unit.faction_secondary_hex = rebel_faction.secondary_hex
            unit._rgba_color = unit._hex_to_rgba(rebel_faction.color_hex)
            unit._rgba_secondary = unit._hex_to_rgba(rebel_faction.secondary_hex)
            faction.remove_unit(unit)
            rebel_faction.add_unit(unit)

        # 资源点争夺
        self._try_grab_resource(faction, rebel_faction)

        # 分配资源
        faction.spend(wood=self.config.rebel_initial_wood, ore=self.config.rebel_initial_ore)
        rebel_faction.add_wood(self.config.rebel_initial_wood)
        rebel_faction.add_ore(self.config.rebel_initial_ore)

        # 重置矛盾值和设置冷却
        faction.conflict_score = 0.0
        rebel_faction.conflict_score = 0.0
        faction.schism_cooldown = self.config.schism_cooldown
        rebel_faction.schism_cooldown = self.config.schism_cooldown

        # 将叛军阵营加入世界
        self.world.factions.append(rebel_faction)

        # 日志
        from src.game_logging.behavior_log import log_schism
        log_schism(faction.name, rebel_faction.name, split_count, faction.alive_count)

    def _create_rebel_faction(self, original: Faction) -> Faction:
        """创建叛军阵营."""
        from src.core.config import FactionConfig

        original_color = original.color_hex
        rebel_primary, rebel_secondary = REBEL_COLORS.get(
            original_color,
            ("#AAFFAA", "#CCFFCC"),  # 默认绿色
        )

        rebel_config = FactionConfig(
            name=f"{original.name}·叛军",
            color_hex=rebel_primary,
            secondary_color_hex=rebel_secondary,
            initial_wood=0,
            initial_ore=0,
            initial_units=0,
            max_units=original.config.max_units,
            unit_hp=original.config.unit_hp,
            move_speed=original.config.move_speed,
            climb_speed=original.config.climb_speed,
            fist_damage=original.config.fist_damage,
            gather_speed=original.config.gather_speed,
        )

        rebel = Faction(config=rebel_config)
        rebel.is_rebel = True
        rebel.parent_faction_name = original.name
        rebel.spawn_x = original.spawn_x
        rebel.spawn_y = original.spawn_y

        return rebel

    def _try_grab_resource(self, original: Faction, rebel: Faction) -> None:
        """叛军尝试抢占原阵营的资源点."""
        from src.game_logging.behavior_log import log_schism_resource_grab

        # 找原阵营的资源点
        resource_nodes = [
            rn for rn in self.world.resource_nodes
            if rn.faction_name == original.name
        ]

        if not resource_nodes:
            log_schism_resource_grab(rebel.name, "none", False)
            return

        # 优先选离叛军单位最近的
        if rebel.alive_units and rebel.alive_units[0].body is not None:
            rebel_x = rebel.alive_units[0].body.position.x
            resource_nodes.sort(
                key=lambda rn: abs(rn.screen_x - rebel_x)
                if hasattr(rn, "screen_x") else 0,
            )

        target_node = resource_nodes[0]

        # 争夺概率
        if random.random() < self.config.resource_grab_probability:
            # 成功: 转移资源点
            target_node.faction_name = rebel.name
            target_node.color_hex = rebel.color_hex
            target_node.secondary_color_hex = rebel.secondary_hex
            original.resource_nodes = [
                rn for rn in getattr(original, "resource_nodes", [])
                if rn.node_id != target_node.node_id
            ]
            log_schism_resource_grab(rebel.name, target_node.resource_type, True)
        else:
            log_schism_resource_grab(rebel.name, target_node.resource_type, False)
