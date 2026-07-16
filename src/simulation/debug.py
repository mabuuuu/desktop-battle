"""Desktop Battle - 调试模式.

允许手动指定小人行为，用于测试:
- 选中指定小人
- 强制指定行为（采集/战斗/巡逻/建造等）
- 查看小人状态信息
- 快捷键操作

通过系统托盘菜单"调试模式"开关。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.entity.unit import Unit
    from src.core.world import World


@dataclass
class DebugState:
    """调试模式状态."""

    enabled: bool = False
    selected_unit_id: int | None = None
    forced_action: str | None = None  # 强制行为
    show_perception: bool = True   # 显示感知范围
    show_roles: bool = True        # 显示角色标签
    show_debug_info: bool = True   # 显示调试信息


class DebugSystem:
    """调试系统管理器.

    提供调试相关的渲染和控制功能。
    """

    def __init__(self, world: World) -> None:
        self._world = world
        self.state = DebugState()

    def toggle(self) -> bool:
        """切换调试模式."""
        self.state.enabled = not self.state.enabled
        return self.state.enabled

    def select_unit(self, screen_x: float, screen_y: float) -> Unit | None:
        """点击选中最近的小人."""
        nearest_unit = None
        nearest_dist = 20.0  # 20px选择范围

        for unit in self._world.units:
            if not unit.alive:
                continue
            ux, uy = unit.screen_position(self._world.screen_height)
            dist = ((screen_x - ux) ** 2 + (screen_y - uy) ** 2) ** 0.5
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_unit = unit

        if nearest_unit is not None:
            self.state.selected_unit_id = nearest_unit.unit_id
        return nearest_unit

    def force_action(self, action: str) -> None:
        """强制选中单位执行某行为.

        Args:
            action: 行为名称
                "idle" / "walk" / "mine" / "fight" / "flee" /
                "patrol" / "scout" / "build" / "craft" / "carry" / "reset"
        """
        if self.state.selected_unit_id is None:
            return

        unit = self._find_unit(self.state.selected_unit_id)
        if unit is None or not unit.alive:
            return

        from src.entity.unit import UnitState, UnitRole

        if action == "reset":
            self.state.forced_action = None
            unit.state = UnitState.IDLE
            return

        self.state.forced_action = action

        # 直接设置状态
        state_map = {
            "idle": UnitState.IDLE,
            "walk": UnitState.WALKING,
            "mine": UnitState.MINING,
            "fight": UnitState.FIGHTING,
            "flee": UnitState.FLEEING,
            "patrol": UnitState.PATROLLING,
            "scout": UnitState.SCOUTING,
            "build": UnitState.BUILDING,
            "craft": UnitState.CRAFTING,
            "carry": UnitState.CARRYING,
        }
        if action in state_map:
            unit.state = state_map[action]

        # 角色切换
        role_map = {
            "mine": ("gatherer", UnitRole.GATHERER),
            "fight": ("soldier", UnitRole.SOLDIER),
            "patrol": ("soldier", UnitRole.SOLDIER),
            "scout": ("scout", UnitRole.SCOUT),
            "build": ("builder", UnitRole.BUILDER),
            "craft": ("builder", UnitRole.BUILDER),
        }
        if action in role_map:
            role_str, role_enum = role_map[action]
            unit.role = role_enum
            bb = self._world._faction_blackboards.get(unit.faction_name)
            if bb is not None:
                bb.assign_role(unit.unit_id, role_str)

    def render_debug_overlay(self, buffer: np.ndarray) -> None:
        """渲染调试覆盖层."""
        if not self.state.enabled:
            return

        from src.render.sprite import draw_line, draw_circle, draw_text

        for unit in self._world.units:
            if not unit.alive:
                continue

            sx, sy = unit.screen_position(self._world.screen_height)

            # 选中高亮
            if unit.unit_id == self.state.selected_unit_id:
                draw_circle(buffer, sx, sy - 10, 14, (255, 255, 0, 120), 1)

            # 感知范围
            if self.state.show_perception:
                from src.simulation.perception import PerceptionConfig
                cfg = PerceptionConfig()
                # 前方视野弧线（简化为水平线）
                if unit.facing_right:
                    draw_line(buffer, sx, sy - 10, sx + cfg.forward_range, sy - 10,
                              (100, 100, 255, 60), 1)
                else:
                    draw_line(buffer, sx - cfg.forward_range, sy - 10, sx, sy - 10,
                              (100, 100, 255, 60), 1)
                # 听觉范围
                draw_circle(buffer, sx, sy - 10, int(cfg.hearing_range), (80, 80, 80, 40), 1)

            # 角色标签
            if self.state.show_roles:
                from src.entity.unit import UnitRole
                role_char = {
                    UnitRole.GATHERER: "G",
                    UnitRole.BUILDER: "B",
                    UnitRole.SOLDIER: "S",
                    UnitRole.SCOUT: "R",
                    UnitRole.IDLE: "?",
                }.get(unit.role, "?")
                draw_text(buffer, sx - 2, sy - 22, role_char, (255, 255, 0, 200), 8)

        # 选中单位的详细信息
        if self.state.show_debug_info and self.state.selected_unit_id is not None:
            self._render_unit_info(buffer)

    def _render_unit_info(self, buffer: np.ndarray) -> None:
        """渲染选中单位的详细信息."""
        unit = self._find_unit(self.state.selected_unit_id)
        if unit is None:
            return

        from src.render.sprite import draw_rect

        # 信息框
        info_x, info_y = 10, self._world.screen_height - 80
        draw_rect(buffer, float(info_x), float(info_y), 200, 70, (10, 10, 30, 200), 0)
        draw_rect(buffer, float(info_x), float(info_y), 200, 70, (80, 80, 120, 200), 1)

        overlay = getattr(self._world, 'overlay', None)
        if overlay is not None:
            from src.entity.unit import UnitRole
            role_name = {
                UnitRole.GATHERER: "生产者",
                UnitRole.BUILDER: "建造者",
                UnitRole.SOLDIER: "战士",
                UnitRole.SCOUT: "侦察",
                UnitRole.IDLE: "空闲",
            }.get(unit.role, "未知")
            overlay.draw_text(info_x + 5, info_y + 3, f"#{unit.unit_id} {unit.faction_name}", (200, 200, 255, 255), 11.0)
            overlay.draw_text(info_x + 5, info_y + 18, f"角色:{role_name} 状态:{unit.state.value}", (180, 180, 220, 220), 10.0)
            overlay.draw_text(info_x + 5, info_y + 33, f"HP:{unit.hp:.0f}/{unit.max_hp:.0f} 携带:木{unit.carrying_wood}矿{unit.carrying_ore}", (180, 180, 220, 220), 10.0)
            weapon_name = "无"
            if unit.weapon is not None:
                try:
                    weapon_name = unit.weapon.spec.name  # type: ignore
                except AttributeError:
                    weapon_name = "有"
            overlay.draw_text(info_x + 5, info_y + 48, f"武器:{weapon_name} 朝向:{'右' if unit.facing_right else '左'}", (180, 180, 220, 220), 10.0)

            # 拟真系统信息
            simulation = getattr(self._world, 'simulation', None)
            if simulation is not None:
                mind = simulation.get_mind(unit.unit_id)
                emotion_cn = {
                    "calm": "平静", "alert": "警觉", "fearful": "恐惧",
                    "brave": "勇敢", "hesitant": "犹豫",
                }.get(mind.emotion.value, mind.emotion.value)
                overlay.draw_text(info_x + 5, info_y + 63, f"士气:{mind.morale:.1f} 情绪:{emotion_cn}", (160, 160, 200, 200), 10.0)

    def render_debug_overlay_overlay(self, overlay: object) -> None:
        """使用overlay直接API渲染调试覆盖层（高性能）."""
        if not self.state.enabled:
            return

        for unit in self._world.units:
            if not unit.alive:
                continue

            sx, sy = unit.screen_position(self._world.screen_height)
            isx, isy = int(round(sx)), int(round(sy))

            # 选中高亮
            if unit.unit_id == self.state.selected_unit_id:
                overlay.draw_circle(isx, isy - 10, 14, (255, 255, 0, 120), 1)

            # 感知范围
            if self.state.show_perception:
                from src.simulation.perception import PerceptionConfig
                cfg = PerceptionConfig()
                if unit.facing_right:
                    overlay.draw_line(isx, isy - 10, isx + int(cfg.forward_range), isy - 10,
                                      (100, 100, 255, 60), 1)
                else:
                    overlay.draw_line(isx - int(cfg.forward_range), isy - 10, isx, isy - 10,
                                      (100, 100, 255, 60), 1)
                overlay.draw_circle(isx, isy - 10, int(cfg.hearing_range), (80, 80, 80, 40), 1)

            # 角色标签
            if self.state.show_roles:
                from src.entity.unit import UnitRole
                role_char = {
                    UnitRole.GATHERER: "G",
                    UnitRole.BUILDER: "B",
                    UnitRole.SOLDIER: "S",
                    UnitRole.SCOUT: "R",
                    UnitRole.IDLE: "?",
                }.get(unit.role, "?")
                overlay.draw_text(isx - 2, isy - 22, role_char, (255, 255, 0, 200), 8.0)

        # 选中单位的详细信息
        if self.state.show_debug_info and self.state.selected_unit_id is not None:
            self._render_unit_info_overlay(overlay)

    def _render_unit_info_overlay(self, overlay: object) -> None:
        """使用overlay直接API渲染选中单位的详细信息（高性能）."""
        unit = self._find_unit(self.state.selected_unit_id)
        if unit is None:
            return

        info_x, info_y = 10, self._world.screen_height - 80
        overlay.draw_rect(info_x, info_y, 200, 70, (10, 10, 30, 200), 0)
        overlay.draw_rect(info_x, info_y, 200, 70, (80, 80, 120, 200), 1)

        from src.entity.unit import UnitRole
        role_name = {
            UnitRole.GATHERER: "生产者",
            UnitRole.BUILDER: "建造者",
            UnitRole.SOLDIER: "战士",
            UnitRole.SCOUT: "侦察",
            UnitRole.IDLE: "空闲",
        }.get(unit.role, "未知")
        overlay.draw_text(info_x + 5, info_y + 3, f"#{unit.unit_id} {unit.faction_name}", (200, 200, 255, 255), 11.0)
        overlay.draw_text(info_x + 5, info_y + 18, f"角色:{role_name} 状态:{unit.state.value}", (180, 180, 220, 220), 10.0)
        overlay.draw_text(info_x + 5, info_y + 33, f"HP:{unit.hp:.0f}/{unit.max_hp:.0f} 携带:木{unit.carrying_wood}矿{unit.carrying_ore}", (180, 180, 220, 220), 10.0)
        weapon_name = "无"
        if unit.weapon is not None:
            try:
                weapon_name = unit.weapon.spec.name  # type: ignore
            except AttributeError:
                weapon_name = "有"
        overlay.draw_text(info_x + 5, info_y + 48, f"武器:{weapon_name} 朝向:{'右' if unit.facing_right else '左'}", (180, 180, 220, 220), 10.0)

        simulation = getattr(self._world, 'simulation', None)
        if simulation is not None:
            mind = simulation.get_mind(unit.unit_id)
            emotion_cn = {
                "calm": "平静", "alert": "警觉", "fearful": "恐惧",
                "brave": "勇敢", "hesitant": "犹豫",
            }.get(mind.emotion.value, mind.emotion.value)
            overlay.draw_text(info_x + 5, info_y + 63, f"士气:{mind.morale:.1f} 情绪:{emotion_cn}", (160, 160, 200, 200), 10.0)

    def _find_unit(self, unit_id: int) -> Unit | None:
        """查找单位."""
        for u in self._world.units:
            if u.unit_id == unit_id:
                return u
        return None
