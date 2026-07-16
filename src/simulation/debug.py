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

    def _render_control_panel_overlay(self, overlay: object) -> None:
        """渲染调试控制面板（屏幕右侧，显示快捷键和行为按钮）."""
        w = self._world.screen_width
        h = self._world.screen_height
        panel_x = w - 140
        panel_y = 10
        panel_w = 130
        panel_h = 310

        # 背景
        overlay.draw_rect(panel_x, panel_y, panel_w, panel_h, (10, 10, 30, 180), 0)
        overlay.draw_rect(panel_x, panel_y, panel_w, panel_h, (80, 80, 120, 200), 1)

        # 标题
        overlay.draw_text(panel_x + 5, panel_y + 3, "Debug Panel", (200, 200, 255, 255), 11.0)

        y = panel_y + 22
        # 行为按钮提示
        buttons = [
            ("1", "Idle", (180, 180, 180)),
            ("2", "Walk", (100, 255, 100)),
            ("3", "Mine", (200, 200, 68)),
            ("4", "Fight", (255, 80, 80)),
            ("5", "Flee", (255, 200, 100)),
            ("6", "Patrol", (100, 180, 255)),
            ("7", "Scout", (180, 100, 255)),
            ("8", "Build", (200, 160, 100)),
            ("9", "Craft", (160, 200, 200)),
            ("0", "Reset", (255, 255, 255)),
        ]

        for key, label, color in buttons:
            r, g, b = color
            overlay.draw_text(panel_x + 5, y, f"[{key}] {label}", (r, g, b, 220), 10.0)
            y += 18

        # 分隔线
        y += 4
        overlay.draw_line(panel_x + 5, y, panel_x + panel_w - 5, y, (80, 80, 120, 150), 1)
        y += 6

        # 角色切换
        overlay.draw_text(panel_x + 5, y, "Role:", (200, 200, 255, 220), 10.0)
        y += 15
        roles = [
            ("Q", "Gatherer", (68, 204, 68)),
            ("W", "Builder", (200, 160, 68)),
            ("E", "Soldier", (255, 68, 68)),
            ("R", "Scout", (180, 100, 255)),
        ]
        for key, label, color in roles:
            r, g, b = color
            overlay.draw_text(panel_x + 5, y, f"[{key}] {label}", (r, g, b, 220), 10.0)
            y += 15

        # 当前选中单位信息
        if self.state.selected_unit_id is not None:
            y += 4
            overlay.draw_line(panel_x + 5, y, panel_x + panel_w - 5, y, (80, 80, 120, 150), 1)
            y += 4
            unit = self._find_unit(self.state.selected_unit_id)
            if unit is not None:
                overlay.draw_text(panel_x + 5, y, f"Selected: #{unit.unit_id}", (255, 255, 0, 255), 10.0)
                y += 14
                overlay.draw_text(panel_x + 5, y, f"State: {unit.state.value}", (180, 220, 180, 220), 9.0)
                y += 13
                overlay.draw_text(panel_x + 5, y, f"Role: {unit.role.value}", (180, 180, 220, 220), 9.0)

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

        # 调试控制面板（右侧）
        self._render_control_panel_overlay(overlay)

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


class DebugController:
    """AI 调试控制器 — 暴露结构化 API 供外部(AI)实时操控游戏.

    用法:
        ctrl = DebugController(world)
        ctrl.select(3)                    # 选中3号单位
        ctrl.move_to(800, 500)            # 移动到屏幕坐标
        ctrl.force_state("fighting")      # 强制战斗状态
        ctrl.give_resources("红方", 100, 50)  # 给红方加资源
        info = ctrl.snapshot()            # 获取状态快照
    """

    def __init__(self, world: World) -> None:
        self._world = world

    # ── 查询 ──

    def snapshot(self) -> dict:
        """获取完整游戏状态快照."""
        w = self._world
        return {
            "elapsed": round(w.elapsed_time, 1),
            "screen": f"{w.screen_width}x{w.screen_height}",
            "factions": [self._faction_info(f) for f in w.factions],
            "units": [self._unit_info(u) for u in w.units if u.alive],
            "buildings": [self._building_info(b) for b in w.buildings],
        }

    def unit_status(self, unit_id: int) -> dict | None:
        """查询单个单位状态."""
        u = self._find_unit(unit_id)
        return self._unit_info(u) if u else None

    def find_units(self, faction: str | None = None, role: str | None = None, state: str | None = None) -> list[dict]:
        """按条件查找单位."""
        results = []
        for u in self._world.units:
            if not u.alive:
                continue
            if faction and u.faction_name != faction:
                continue
            if role and u.role.value != role:
                continue
            if state and u.state.value != state:
                continue
            results.append(self._unit_info(u))
        return results

    # ── 选中 ──

    def select(self, unit_id: int) -> dict | None:
        """选中单位."""
        u = self._find_unit(unit_id)
        if u is None:
            return None
        self._world.debug.state.selected_unit_id = unit_id
        return self._unit_info(u)

    def deselect(self) -> None:
        """取消选中."""
        self._world.debug.state.selected_unit_id = None

    # ── 移动 ──

    def move_to(self, unit_id: int, screen_x: float) -> dict:
        """移动单位到屏幕X坐标."""
        u = self._find_unit(unit_id)
        if u is None or not u.alive:
            return {"error": f"unit {unit_id} not found or dead"}
        from src.entity.unit import UnitState
        u.state = UnitState.WALKING
        u.move_toward(screen_x)
        return {"action": "move", "unit": unit_id, "target_x": screen_x}

    def move_to_enemy_base(self, unit_id: int) -> dict:
        """移动单位到敌方基地."""
        u = self._find_unit(unit_id)
        if u is None or not u.alive:
            return {"error": f"unit {unit_id} not found or dead"}
        bb = self._world._faction_blackboards.get(u.faction_name)
        target_x = bb.enemy_base_x if bb else self._world.screen_width * 0.8
        from src.entity.unit import UnitState
        u.state = UnitState.WALKING
        u.move_toward(target_x)
        return {"action": "move_to_enemy_base", "unit": unit_id, "target_x": target_x}

    # ── 状态 ──

    def force_state(self, unit_id: int, state: str) -> dict:
        """强制设置单位状态.

        state: idle/walking/mining/fighting/fleeing/climbing/building/
               crafting/carrying/patrolling/scouting/arguing/dying
        """
        u = self._find_unit(unit_id)
        if u is None or not u.alive:
            return {"error": f"unit {unit_id} not found or dead"}
        from src.entity.unit import UnitState
        state_map = {s.value: s for s in UnitState}
        if state not in state_map:
            return {"error": f"unknown state '{state}', valid: {list(state_map.keys())}"}
        u.state = state_map[state]
        return {"action": "force_state", "unit": unit_id, "state": state}

    def reset_state(self, unit_id: int) -> dict:
        """重置单位状态为idle."""
        return self.force_state(unit_id, "idle")

    # ── 角色 ──

    def set_role(self, unit_id: int, role: str) -> dict:
        """设置单位角色并重建行为树.

        role: gatherer/builder/soldier/scout/idle
        """
        u = self._find_unit(unit_id)
        if u is None or not u.alive:
            return {"error": f"unit {unit_id} not found or dead"}
        from src.entity.unit import UnitRole
        role_map = {
            "gatherer": UnitRole.GATHERER,
            "builder": UnitRole.BUILDER,
            "soldier": UnitRole.SOLDIER,
            "scout": UnitRole.SCOUT,
            "idle": UnitRole.IDLE,
        }
        if role not in role_map:
            return {"error": f"unknown role '{role}', valid: {list(role_map.keys())}"}
        u.role = role_map[role]
        bb = self._world._faction_blackboards.get(u.faction_name)
        if bb is not None:
            bb.assign_role(unit_id, role)
        self._world._create_bt_for_unit(u)
        return {"action": "set_role", "unit": unit_id, "role": role}

    # ── 战斗 ──

    def attack(self, attacker_id: int, target_id: int) -> dict:
        """强制攻击目标."""
        attacker = self._find_unit(attacker_id)
        target = self._find_unit(target_id)
        if attacker is None or not attacker.alive:
            return {"error": f"attacker {attacker_id} not found or dead"}
        if target is None or not target.alive:
            return {"error": f"target {target_id} not found or dead"}
        from src.entity.unit import UnitState
        attacker.state = UnitState.FIGHTING
        attacker.combat_target_id = target_id
        # 面向目标
        ax, _ = attacker.screen_position(self._world.screen_height)
        tx, _ = target.screen_position(self._world.screen_height)
        attacker.facing_right = tx >= ax
        return {"action": "attack", "attacker": attacker_id, "target": target_id}

    def stop_attack(self, unit_id: int) -> dict:
        """停止攻击."""
        u = self._find_unit(unit_id)
        if u is None:
            return {"error": f"unit {unit_id} not found"}
        u.combat_target_id = None
        from src.entity.unit import UnitState
        u.state = UnitState.IDLE
        return {"action": "stop_attack", "unit": unit_id}

    # ── 资源 ──

    def give_resources(self, faction_name: str, wood: int = 0, ore: int = 0) -> dict:
        """给阵营加资源."""
        for f in self._world.factions:
            if f.name == faction_name:
                f.wood += wood
                f.ore += ore
                return {"action": "give_resources", "faction": faction_name, "wood": f.wood, "ore": f.ore}
        return {"error": f"faction '{faction_name}' not found"}

    # ── 生成 ──

    def spawn_unit(self, faction_name: str, screen_x: float | None = None, role: str = "soldier") -> dict:
        """在指定位置生成单位."""
        faction = None
        for f in self._world.factions:
            if f.name == faction_name:
                faction = f
                break
        if faction is None:
            return {"error": f"faction '{faction_name}' not found"}
        if faction.alive_count >= faction.config.max_units:
            return {"error": f"faction {faction_name} at max units ({faction.config.max_units})"}

        sx = screen_x if screen_x is not None else faction.spawn_x
        sy = faction.spawn_y
        from src.desktop.coord import screen_to_physics
        px, py = screen_to_physics(sx, sy, self._world.screen_height)
        unit = self._world._create_unit(faction, px, py)
        bb = self._world._faction_blackboards.get(faction_name)
        if bb is not None:
            bb.assign_role(unit.unit_id, role)
        self._world._create_bt_for_unit(unit)
        return {"action": "spawn", "unit_id": unit.unit_id, "faction": faction_name, "role": role}

    def kill_unit(self, unit_id: int) -> dict:
        """杀死单位."""
        u = self._find_unit(unit_id)
        if u is None:
            return {"error": f"unit {unit_id} not found"}
        u.hp = 0
        u.alive = False
        from src.entity.unit import UnitState
        u.state = UnitState.DYING
        return {"action": "kill", "unit": unit_id}

    def heal_unit(self, unit_id: int, hp: float | None = None) -> dict:
        """治疗单位（默认满血）."""
        u = self._find_unit(unit_id)
        if u is None:
            return {"error": f"unit {unit_id} not found"}
        u.hp = hp if hp is not None else u.max_hp
        u.alive = True
        from src.entity.unit import UnitState
        if u.state == UnitState.DYING:
            u.state = UnitState.IDLE
        return {"action": "heal", "unit": unit_id, "hp": u.hp}

    # ── 暂停 ──

    def pause(self) -> dict:
        """暂停游戏."""
        # 通过 world 引用找到 game_loop
        loop = getattr(self._world, '_game_loop', None)
        if loop is not None:
            loop.paused = True
            return {"action": "pause", "paused": True}
        return {"error": "game_loop not accessible"}

    def resume(self) -> dict:
        """恢复游戏."""
        loop = getattr(self._world, '_game_loop', None)
        if loop is not None:
            loop.paused = False
            return {"action": "resume", "paused": False}
        return {"error": "game_loop not accessible"}

    # ── 批量操作 ──

    def move_all(self, faction: str, screen_x: float) -> dict:
        """移动某阵营所有单位到指定X坐标."""
        from src.entity.unit import UnitState
        count = 0
        for u in self._world.units:
            if u.alive and u.faction_name == faction:
                u.state = UnitState.WALKING
                u.move_toward(screen_x)
                count += 1
        return {"action": "move_all", "faction": faction, "count": count, "target_x": screen_x}

    def set_all_role(self, faction: str, role: str) -> dict:
        """设置某阵营所有单位角色."""
        count = 0
        for u in self._world.units:
            if u.alive and u.faction_name == faction:
                self.set_role(u.unit_id, role)
                count += 1
        return {"action": "set_all_role", "faction": faction, "role": role, "count": count}

    # ── 内部辅助 ──

    def _find_unit(self, unit_id: int) -> Unit | None:
        for u in self._world.units:
            if u.unit_id == unit_id:
                return u
        return None

    def _unit_info(self, u: Unit) -> dict:
        sx, sy = u.screen_position(self._world.screen_height)
        return {
            "id": u.unit_id,
            "faction": u.faction_name,
            "role": u.role.value,
            "state": u.state.value,
            "hp": round(u.hp, 1),
            "max_hp": round(u.max_hp, 1),
            "pos": [round(sx), round(sy)],
            "facing_right": u.facing_right,
            "wood": u.carrying_wood,
            "ore": u.carrying_ore,
            "weapon": u.weapon.spec.name if u.weapon and hasattr(u.weapon, 'spec') else None,
            "attack_cd": round(u.attack_cooldown, 2),
        }

    def _faction_info(self, f) -> dict:
        return {
            "name": f.name,
            "alive": f.alive_count,
            "wood": f.wood,
            "ore": f.ore,
            "strategy": f.current_strategy,
            "buildings": len(f.buildings),
            "produced": f.units_produced,
            "lost": f.units_lost,
        }

    def _building_info(self, b) -> dict:
        sx, sy = b.screen_position(self._world.screen_height)
        return {
            "id": b.building_id,
            "faction": b.faction_name,
            "type": b.building_type,
            "level": b.level,
            "hp": round(b.hp, 1),
            "pos": [round(sx), round(sy)],
        }
