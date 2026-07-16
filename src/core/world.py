"""Desktop Battle - 世界状态管理.

管理所有阵营、单位、建筑、资源节点、物理引擎。
提供完整的游戏初始化和每帧更新。
集成: 行为树AI, 战斗系统, 攀爬物理, 视觉效果, 日志, AI策略, 阵营分裂。
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

import numpy as np
import pymunk
import py_trees
from loguru import logger

from src.behavior.blackboard import FactionBlackboard
from src.behavior.trees import create_behavior_tree_for_unit
from src.desktop.coord import physics_to_screen, screen_to_physics
from src.desktop.taskbar import get_taskbar_rect
from src.desktop.window_scanner import (
    PlatformData,
    platforms_to_terrain_segments,
    scan_desktop_windows,
)
from src.entity.building import BUILDING_SPECS, Building
from src.entity.faction import Faction
from src.entity.resource_node import ResourceNode
from src.entity.schism import SchismManager
from src.entity.unit import Unit, UnitState
from src.physics.body_factory import create_terrain_segment
from src.physics.engine import CollisionType, PhysicsEngine
from src.render.effects import EffectManager
from src.ui.panel import InfoPanel

if TYPE_CHECKING:
    from src.ai.strategy import AIStrategyManager
    from src.combat.weapon import WeaponInstance
    from src.core.config import GameConfig
    from src.economy.crafting import CraftingManager
    from src.render.overlay import TransparentOverlay


class World:
    """游戏世界状态."""

    def __init__(self, config: GameConfig, overlay: TransparentOverlay) -> None:
        self.config: GameConfig = config
        self.overlay: TransparentOverlay = overlay
        self.screen_width: int = overlay.width
        self.screen_height: int = overlay.height

        # 物理引擎 (pymunk Y轴向上, 重力向下为负值)
        self.physics: PhysicsEngine = PhysicsEngine(
            gravity=(0.0, -self.config.gravity),
            damping=self.config.damping,
            collision_slop=self.config.collision_slop,
            iterations=self.config.physics_iterations,
        )

        # 实体管理
        self.factions: list[Faction] = []
        self.units: list[Unit] = []
        self.buildings: list[Building] = []
        self.resource_nodes: list[ResourceNode] = []
        self.weapons_on_ground: list[WeaponInstance] = []

        # ID 计数器
        self._next_unit_id: int = 1
        self._next_building_id: int = 1
        self._next_resource_id: int = 1
        self._next_weapon_id: int = 1

        # 地形物理体
        self._terrain_bodies: list[tuple[pymunk.Body, list[pymunk.Shape]]] = []

        # 平台 (窗口)
        self._platforms: list[PlatformData] = []
        self._last_scan_time: float = 0.0

        # 制作管理器
        from src.economy.crafting import CraftingManager
        self.crafting: CraftingManager = CraftingManager()

        # 运行时间
        self.elapsed_time: float = 0.0

        # ── Phase 7: 行为树 ──
        self._unit_behavior_trees: dict[int, py_trees.behaviour.Behaviour] = {}
        self._faction_blackboards: dict[str, FactionBlackboard] = {}
        self._behavior_tick_counter: int = 0

        # ── Phase 8: 视觉效果 ──
        self.effect_manager: EffectManager = EffectManager()

        # ── Phase 10: 日志系统 ──
        self._logs_initialized: bool = False

        # ── Phase 11: 面板 ──
        self._panel: InfoPanel | None = None

        # ── Phase 12: AI 策略 ──
        self._ai_manager: AIStrategyManager | None = None
        self._damage_multiplier: float = 1.0

        # ── Phase 14: 阵营分裂 ──
        self.schism_manager: SchismManager = SchismManager(self)

        # ── 拟真系统 ──
        from src.simulation.realism import SimulationSystem
        from src.simulation.events import EventBus
        from src.simulation.debug import DebugSystem
        self.simulation: SimulationSystem = SimulationSystem(self)
        self.event_bus: EventBus = EventBus()
        self.debug: DebugSystem = DebugSystem(self)

        # AI 调试控制器
        from src.simulation.debug import DebugController
        self.debug_ctrl: DebugController = DebugController(self)

        # 初始化碰撞回调
        self._setup_collision_handlers()

    def _setup_collision_handlers(self) -> None:
        """设置碰撞回调 (pymunk >= 7.0)."""

        def unit_terrain_begin(
            arbiter: pymunk.Arbiter, space: pymunk.Space, data: object
        ) -> None:
            shapes = arbiter.shapes
            for s in shapes:
                if s.collision_type == CollisionType.UNIT and hasattr(s, "data"):
                    unit = s.data
                    if isinstance(unit, Unit):
                        unit.on_ground = True

        def unit_terrain_separate(
            arbiter: pymunk.Arbiter, space: pymunk.Space, data: object
        ) -> None:
            shapes = arbiter.shapes
            for s in shapes:
                if s.collision_type == CollisionType.UNIT and hasattr(s, "data"):
                    unit = s.data
                    if isinstance(unit, Unit):
                        unit.on_ground = False

        self.physics.add_collision_handler(
            CollisionType.UNIT,
            CollisionType.TERRAIN,
            begin=unit_terrain_begin,
            separate=unit_terrain_separate,
        )

        # 单位间碰撞 (战斗触发)
        def unit_unit_begin(
            arbiter: pymunk.Arbiter, space: pymunk.Space, data: object
        ) -> None:
            shapes = arbiter.shapes
            u1: Unit | None = None
            u2: Unit | None = None
            for s in shapes:
                if s.collision_type == CollisionType.UNIT and hasattr(s, "data"):
                    u = s.data
                    if isinstance(u, Unit):
                        if u1 is None:
                            u1 = u
                        else:
                            u2 = u
            if u1 is not None and u2 is not None and u1.faction_name != u2.faction_name:
                # 敌方单位接触 → 记录在黑板供行为树使用
                pass

        self.physics.add_collision_handler(
            CollisionType.UNIT,
            CollisionType.UNIT,
            begin=unit_unit_begin,
        )

    def initialize(self) -> None:
        """初始化游戏世界: 创建地形、阵营、单位."""
        # 1. 创建任务栏地面
        self._create_taskbar_ground()

        # 2. 扫描桌面窗口 → 平台
        self._scan_and_create_platforms()

        # 3. 创建阵营
        taskbar_rect = get_taskbar_rect()
        ground_screen_y: float = float(taskbar_rect.top) if taskbar_rect else float(self.screen_height - 40)

        for i, faction_cfg in enumerate(self.config.factions):
            faction = Faction(config=faction_cfg)
            faction.wood = faction_cfg.initial_wood
            faction.ore = faction_cfg.initial_ore

            # 出生点: 两阵营分列屏幕两侧
            if i == 0:
                spawn_screen_x = self.screen_width * 0.2
            else:
                spawn_screen_x = self.screen_width * 0.8

            spawn_screen_y = ground_screen_y - 10
            spawn_phys_x, spawn_phys_y = screen_to_physics(
                spawn_screen_x, spawn_screen_y, self.screen_height
            )

            faction.spawn_x = spawn_screen_x
            faction.spawn_y = spawn_screen_y

            # 创建阵营黑板
            bb = FactionBlackboard(faction_name=faction.name)
            bb.rally_point = (spawn_screen_x, spawn_screen_y)
            if i == 0:
                bb.enemy_base_x = self.screen_width * 0.8
            else:
                bb.enemy_base_x = self.screen_width * 0.2
            self._faction_blackboards[faction.name] = bb

            # 创建初始单位
            for j in range(faction_cfg.initial_units):
                offset_x = j * 15 - (faction_cfg.initial_units * 7)
                ux = spawn_screen_x + offset_x
                uy = spawn_screen_y
                upx, upy = screen_to_physics(ux, uy, self.screen_height)
                unit = self._create_unit(faction, upx, upy)
                # 创建行为树
                self._create_bt_for_unit(unit)
                # 分配角色
                role = "gatherer" if j < 2 else "soldier"
                bb.assign_role(unit.unit_id, role)

            # 创建资源采集点
            wood_node_x = spawn_screen_x - 30
            ore_node_x = spawn_screen_x + 30
            node_y = spawn_screen_y
            wnpx, wnpy = screen_to_physics(wood_node_x, node_y, self.screen_height)
            onpx, onpy = screen_to_physics(ore_node_x, node_y, self.screen_height)

            wood_node = self._create_resource_node(
                faction, "wood", wnpx, wnpy,
                "#44CC44" if faction.name == "红方" else "#44AAFF",
                "#88EE88" if faction.name == "红方" else "#88CCFF",
            )
            ore_node = self._create_resource_node(
                faction, "ore", onpx, onpy,
                "#CCAA44" if faction.name == "红方" else "#CCAA44",
                "#EECC66" if faction.name == "红方" else "#EECC66",
            )

            self.factions.append(faction)

        # 初始化日志
        self._init_logging()

        # 初始化AI策略管理器
        self._init_ai_manager()

        # 初始化面板
        self._panel = InfoPanel(self)

    def _create_bt_for_unit(self, unit: Unit) -> None:
        """为单位创建行为树（根据角色）."""
        from src.behavior.trees import create_behavior_tree_for_role
        role = self._get_unit_role(unit)
        bt = create_behavior_tree_for_role(role, unit.unit_id, f"U{unit.unit_id}")
        # 设置黑板
        bt_bb = py_trees.blackboard.Blackboard()
        bt_bb.set("unit", unit)
        bt_bb.set("world", self)
        bt_bb.set("faction_bb", self._faction_blackboards.get(unit.faction_name))
        self._unit_behavior_trees[unit.unit_id] = bt

    def _get_unit_role(self, unit: Unit) -> str:
        """获取单位当前角色."""
        bb = self._faction_blackboards.get(unit.faction_name)
        if bb is not None:
            return bb.get_role(unit.unit_id)
        return "idle"

    def _rebuild_bt_if_role_changed(self, unit: Unit) -> None:
        """如果角色变更，重建行为树."""
        from src.entity.unit import UnitRole
        current_role = self._get_unit_role(unit)
        old_role = unit.role.value
        if current_role != old_role:
            # 更新unit的role字段
            role_map = {
                "gatherer": UnitRole.GATHERER,
                "builder": UnitRole.BUILDER,
                "soldier": UnitRole.SOLDIER,
                "scout": UnitRole.SCOUT,
                "idle": UnitRole.IDLE,
            }
            unit.role = role_map.get(current_role, UnitRole.IDLE)
            # 重建行为树
            self._create_bt_for_unit(unit)

    def _init_logging(self) -> None:
        """初始化日志系统."""
        if self._logs_initialized:
            return
        try:
            from src.game_logging.logger import init_logging
            init_logging()
            from src.game_logging.system_log import log_game_start
            log_game_start(f"Factions={len(self.factions)} Units={len(self.units)}")
            self._logs_initialized = True
        except Exception:
            pass

    def _init_ai_manager(self) -> None:
        """初始化AI策略管理器."""
        if not self.config.ai.enabled:
            return
        try:
            from src.ai.strategy import AIStrategyManager
            self._ai_manager = AIStrategyManager(
                world=self,
                api_key=self.config.ai.api_key,
                api_url=self.config.ai.api_url,
                model=self.config.ai.model,
                interval=self.config.ai.strategy_interval,
                timeout=self.config.ai.timeout,
            )
            for f_name, bb in self._faction_blackboards.items():
                self._ai_manager.set_blackboard(f_name, bb)
        except Exception as e:
            logger.warning(f"AI manager init failed: {e}")

    @property
    def panel(self) -> InfoPanel | None:
        return self._panel

    def set_damage_multiplier(self, multiplier: float) -> None:
        """设置全局伤害倍率."""
        self._damage_multiplier = multiplier

    def _create_taskbar_ground(self) -> None:
        """创建任务栏地面物理体."""
        rect = get_taskbar_rect()
        if rect is None:
            p1 = screen_to_physics(0.0, float(self.screen_height - 40), self.screen_height)
            p2 = screen_to_physics(float(self.screen_width), float(self.screen_height - 40), self.screen_height)
        else:
            p1 = screen_to_physics(float(rect.left), float(rect.top), self.screen_height)
            p2 = screen_to_physics(float(rect.right), float(rect.top), self.screen_height)

        body, shape = create_terrain_segment(
            x1=p1[0], y1=p1[1], x2=p2[0], y2=p2[1],
            friction=self.config.terrain_friction,
            elasticity=self.config.terrain_elasticity,
            radius=3.0,
        )
        self.physics.add_body(body, shape)
        self._terrain_bodies.append((body, [shape]))

        # 创建左右边界墙（防止小人移出屏幕）
        self._create_boundary_walls()

    def _create_boundary_walls(self) -> None:
        """创建屏幕左右边界墙."""
        # 左边界墙
        p1_left = screen_to_physics(0.0, 0.0, self.screen_height)
        p2_left = screen_to_physics(0.0, float(self.screen_height), self.screen_height)
        body_left, shape_left = create_terrain_segment(
            x1=p1_left[0], y1=p1_left[1], x2=p2_left[0], y2=p2_left[1],
            friction=self.config.terrain_friction,
            elasticity=self.config.terrain_elasticity,
            radius=2.0,
        )
        self.physics.add_body(body_left, shape_left)
        self._terrain_bodies.append((body_left, [shape_left]))

        # 右边界墙
        p1_right = screen_to_physics(float(self.screen_width), 0.0, self.screen_height)
        p2_right = screen_to_physics(float(self.screen_width), float(self.screen_height), self.screen_height)
        body_right, shape_right = create_terrain_segment(
            x1=p1_right[0], y1=p1_right[1], x2=p2_right[0], y2=p2_right[1],
            friction=self.config.terrain_friction,
            elasticity=self.config.terrain_elasticity,
            radius=2.0,
        )
        self.physics.add_body(body_right, shape_right)
        self._terrain_bodies.append((body_right, [shape_right]))

    def _scan_and_create_platforms(self) -> None:
        """扫描窗口并创建平台物理体."""
        scan_start = time.time()
        windows = scan_desktop_windows()
        self._platforms = windows
        segments = platforms_to_terrain_segments(windows, self.screen_height)

        for p1, p2 in segments:
            body, shape = create_terrain_segment(
                x1=p1[0], y1=p1[1], x2=p2[0], y2=p2[1],
                friction=1.0,
                elasticity=0.05,
                radius=1.5,
            )
            self.physics.add_body(body, shape)
            self._terrain_bodies.append((body, [shape]))

        scan_time = (time.time() - scan_start) * 1000
        try:
            from src.game_logging.system_log import log_window_scan
            log_window_scan(len(windows), scan_time)
        except Exception:
            pass

    def _create_unit(self, faction: Faction, phys_x: float, phys_y: float) -> Unit:
        """创建单位."""
        unit = Unit(
            unit_id=self._next_unit_id,
            faction_name=faction.name,
            faction_color_hex=faction.color_hex,
            faction_secondary_hex=faction.secondary_hex,
            config=self.config,
            faction_cfg=faction.config,
            hp=float(faction.config.unit_hp),
            max_hp=float(faction.config.unit_hp),
            move_speed=faction.config.move_speed,
            perception_range=self.config.unit_perception_range,
        )
        self._next_unit_id += 1
        unit.init_physics(phys_x, phys_y)
        self.units.append(unit)
        faction.add_unit(unit)
        self.physics.add_body(unit.body, unit.shape)
        return unit

    def _create_resource_node(
        self, faction: Faction, resource_type: str,
        phys_x: float, phys_y: float,
        color_hex: str, secondary_hex: str,
    ) -> ResourceNode:
        """创建资源节点."""
        node = ResourceNode(
            node_id=self._next_resource_id,
            faction_name=faction.name,
            resource_type=resource_type,
            color_hex=color_hex,
            secondary_color_hex=secondary_hex,
            screen_height=self.screen_height,
            output_rate=self.config.resource_output_rate,
        )
        self._next_resource_id += 1
        node.init_physics(phys_x, phys_y)
        self.resource_nodes.append(node)
        self.physics.add_body(node.body, node.shape)
        return node

    def create_building(
        self, faction: Faction, building_type: str, level: int,
        phys_x: float, phys_y: float,
    ) -> Building | None:
        """创建建筑."""
        spec = BUILDING_SPECS.get((building_type, level))
        if spec is None:
            return None

        building = Building(
            building_id=self._next_building_id,
            faction_name=faction.name,
            faction_color_hex=faction.color_hex,
            building_type=building_type,
            level=level,
        )
        self._next_building_id += 1
        building.init_physics(phys_x, phys_y)
        self.buildings.append(building)
        faction.add_building(building)
        self.physics.add_body(building.body, building.shape)

        try:
            from src.game_logging.system_log import log_building_created
            log_building_created(building, faction)
        except Exception:
            pass

        return building

    def spawn_unit_from_barracks(
        self, faction: Faction, barracks: Building,
    ) -> Unit | None:
        """从兵营生产一个新单位."""
        if faction.alive_count >= faction.config.max_units:
            return None

        screen_x, screen_y = barracks.screen_position(self.screen_height)
        spawn_screen_y = screen_y
        spawn_screen_x = screen_x + barracks.width // 2
        px, py = screen_to_physics(spawn_screen_x, spawn_screen_y - 5, self.screen_height)

        unit = self._create_unit(faction, px, py)
        faction.units_produced += 1

        # 为新单位创建行为树（根据分配的角色）
        bb = self._faction_blackboards.get(faction.name)
        if bb is not None:
            bb.auto_assign_roles(self.units)
            role = bb.get_role(unit.unit_id)
        else:
            role = "idle"
        # 根据角色创建行为树
        from src.behavior.trees import create_behavior_tree_for_role
        from src.entity.unit import UnitRole
        bt = create_behavior_tree_for_role(role, unit.unit_id, f"U{unit.unit_id}")
        bt_bb = py_trees.blackboard.Blackboard()
        bt_bb.set("unit", unit)
        bt_bb.set("world", self)
        bt_bb.set("faction_bb", bb)
        self._unit_behavior_trees[unit.unit_id] = bt
        # 设置unit角色
        role_map = {
            "gatherer": UnitRole.GATHERER,
            "builder": UnitRole.BUILDER,
            "soldier": UnitRole.SOLDIER,
            "scout": UnitRole.SCOUT,
            "idle": UnitRole.IDLE,
        }
        unit.role = role_map.get(role, UnitRole.IDLE)

        try:
            from src.game_logging.system_log import log_unit_spawned
            log_unit_spawned(faction, unit.unit_id)
        except Exception:
            pass

        return unit

    def update(self, dt: float) -> None:
        """更新世界状态."""
        self.elapsed_time += dt

        # 物理步进
        self.physics.step(self.config.physics_dt)

        # 更新攻击冷却
        from src.combat.attack import update_attack_cooldown
        for unit in self.units:
            if unit.alive:
                update_attack_cooldown(unit, dt)
                unit.update_animation()

        # ── 行为树更新 (每 N 帧) ──
        self._behavior_tick_counter += 1
        if self._behavior_tick_counter >= self.config.behavior_tick_interval:
            self._behavior_tick_counter = 0
            self._update_behavior_trees()

        # ── 攀爬检测 ──
        self._update_climbing(dt)

        # 更新资源节点
        for node in self.resource_nodes:
            node.update(dt)

        # 更新制作系统
        completed_jobs = self.crafting.update(dt)
        for job in completed_jobs:
            self._on_craft_complete(job)

        # 更新掉落武器计时
        for weapon in self.weapons_on_ground:
            weapon.update_lifetime(dt)
        self.weapons_on_ground = [w for w in self.weapons_on_ground if not w.expired]

        # 定期扫描窗口
        self._last_scan_time += dt
        if self._last_scan_time >= self.config.window_scan_interval:
            self._last_scan_time = 0.0
            self._scan_and_create_platforms()

        # ── 兵营自动生产 ──
        self._update_barracks_production(dt)

        # ── AI 策略管理 ──
        if self._ai_manager is not None:
            self._ai_manager.update(dt)
        else:
            # 使用内置规则
            self._update_rules_strategy()

        # 清理死亡单位
        self._cleanup_dead_units()

        # ── 阵营分裂机制 ──
        self.schism_manager.update(dt)
        self.schism_manager.update_arguing_units(dt)

        # ── 拟真系统 ──
        self.simulation.update(dt)

        # ── 事件总线清理 ──
        self.event_bus.cleanup(self.elapsed_time)

        # 更新面板
        if self._panel is not None:
            self._panel.update(self.elapsed_time)

    def _update_behavior_trees(self) -> None:
        """Tick 所有单位的行为树，并检查角色变更."""
        for unit in self.units:
            if not unit.alive:
                continue

            # 检查角色是否变更，如变更则重建行为树
            self._rebuild_bt_if_role_changed(unit)

            bt = self._unit_behavior_trees.get(unit.unit_id)
            if bt is None:
                continue

            try:
                # 刷新黑板中的 unit 引用
                bb = py_trees.blackboard.Blackboard()
                bb.set("unit", unit)
                bb.set("world", self)
                bb.set("faction_bb", self._faction_blackboards.get(unit.faction_name))

                # Tick 行为树
                bt.tick_once()
            except Exception as bt_err:
                logger.debug("BT error for unit {}: {}", unit.unit_id, bt_err)

    def _update_climbing(self, dt: float) -> None:
        """更新攀爬系统."""
        from src.physics.climbing import check_and_start_climbing, update_climbing

        for unit in self.units:
            if not unit.alive:
                continue
            if unit.state == UnitState.CLIMBING:
                update_climbing(unit, dt, self)
            elif unit.on_ground:
                # 只在接地时检测攀爬
                check_and_start_climbing(unit, self)

    def _update_barracks_production(self, dt: float) -> None:
        """更新兵营生产."""
        for faction in self.factions:
            if faction.alive_count < faction.config.max_units:
                barracks_list = faction.get_buildings_by_type("barracks")
                for barracks in barracks_list:
                    from src.economy.production import try_start_production
                    if barracks.can_produce():
                        try_start_production(barracks, faction, self.config)

                for barracks in barracks_list:
                    from src.economy.production import process_barracks_production
                    new_ids = process_barracks_production(
                        barracks, faction, dt, [self._next_unit_id]
                    )
                    for _ in new_ids:
                        self.spawn_unit_from_barracks(faction, barracks)
                        self._next_unit_id += len(new_ids)

    def _update_rules_strategy(self) -> None:
        """使用内置规则更新策略 (无AI时)."""
        for faction in self.factions:
            bb = self._faction_blackboards.get(faction.name)
            if bb is None:
                continue
            alive = faction.alive_count
            wood = faction.wood
            ore = faction.ore
            bench_level = faction.get_workbench_highest_level()

            # 动态策略切换
            if alive < 3:
                bb.current_strategy = "defense"
            elif wood >= 30 and ore >= 10:
                bb.current_strategy = "tech"
            elif alive >= 6:
                bb.current_strategy = "rush"
            else:
                bb.current_strategy = "expand"

            faction.current_strategy = bb.current_strategy

            # 按策略动态分配角色
            bb.auto_assign_roles(self.units)

            # 自动建造
            if bench_level == 0 and wood >= 15:
                bb.add_build_order("workbench", 1,
                    float(faction.spawn_x) + 50,
                    screen_to_physics(faction.spawn_x + 50, faction.spawn_y, self.screen_height)[1])

    def _on_craft_complete(self, job: object) -> None:
        """制作完成回调."""
        from src.combat.weapon import WeaponInstance, get_weapon_spec
        from src.economy.crafting import CraftingJob

        if not isinstance(job, CraftingJob):
            return

        spec = get_weapon_spec(job.weapon_name)
        weapon = WeaponInstance(spec=spec, weapon_id=self._next_weapon_id)
        self._next_weapon_id += 1

        crafter = self._find_unit_by_id(job.crafter_id or 0)
        if crafter is not None:
            sx, sy = crafter.screen_position(self.screen_height)
            weapon.drop(sx + 10, sy - 10)
        else:
            weapon.drop(0.0, 0.0)

        self.weapons_on_ground.append(weapon)

    def _find_unit_by_id(self, unit_id: int) -> Unit | None:
        """根据ID查找单位."""
        for u in self.units:
            if u.unit_id == unit_id:
                return u
        return None

    def _cleanup_dead_units(self) -> None:
        """清理死亡单位."""
        for unit in self.units:
            if not unit.alive and unit.body is not None:
                # 添加死亡粒子效果
                if unit.state == UnitState.DYING:
                    sx, sy = unit.screen_position(self.screen_height)
                    self.effect_manager.add_death_particles(sx, sy,
                        unit._rgba_color)

                # 从物理空间移除
                try:
                    self.physics.remove_body(unit.body, unit.shape)
                except Exception:
                    pass
                unit.body = None
                unit.shape = None

                # 更新阵营统计
                faction = self._find_faction_by_name(unit.faction_name)
                if faction is not None:
                    faction.units_lost += 1

                # 记录死亡
                try:
                    from src.game_logging.behavior_log import log_unit_death
                    killer = self._find_unit_by_id(unit.combat_target_id or 0)
                    log_unit_death(unit, killer)
                except Exception:
                    pass

    def _find_faction_by_name(self, name: str) -> Faction | None:
        """根据名称查找阵营."""
        for f in self.factions:
            if f.name == name:
                return f
        return None

    def render(self, overlay: TransparentOverlay) -> None:
        """渲染所有实体到 overlay（纯 overlay 直接 API，无 numpy 缓冲）."""
        import time as _time
        t0 = _time.perf_counter()

        # 清空overlay（每帧开始）
        overlay.clear_frame()

        t1 = _time.perf_counter()

        # 1. 地形线 (overlay直接API)
        rect = get_taskbar_rect()
        if rect is not None:
            overlay.draw_line(
                rect.left, rect.top, rect.right, rect.top,
                (60, 60, 80, 150), 3,
            )

        t2 = _time.perf_counter()

        # 2. 建筑 (overlay直接API)
        for building in self.buildings:
            building.render_overlay(overlay, self.screen_height)

        t3 = _time.perf_counter()

        # 3. 资源节点 (overlay直接API)
        for node in self.resource_nodes:
            node.render_overlay(overlay, self.screen_height)

        t4 = _time.perf_counter()

        # 5. 单位 (overlay直接API)
        for unit in self.units:
            if unit.alive:
                unit.render_overlay(overlay, self.screen_height)

        t5 = _time.perf_counter()

        # 4. 掉落武器 (overlay直接API)
        for weapon in self.weapons_on_ground:
            self._render_weapon_on_ground_overlay(overlay, weapon)

        # 6. 视觉效果
        # self.effect_manager.update_and_render(buffer, int(self.elapsed_time * 60))

        # 7. HUD (overlay直接API)
        self._render_hud_overlay(overlay)

        # 8. 信息面板
        if self._panel is not None and self._panel.visible:
            self._panel.render_overlay(overlay)

        # 9. 调试覆盖层
        if self.debug.state.enabled:
            self.debug.render_debug_overlay_overlay(overlay)

        t6 = _time.perf_counter()

        # 提交到 overlay
        overlay.signal_render()

        t7 = _time.perf_counter()

        # 性能日志 (每5秒输出一次)
        if not hasattr(self, '_render_log_time'):
            self._render_log_time = 0.0
        self._render_log_time += (t7 - t0)
        if self._render_log_time > 5.0:
            from loguru import logger
            logger.debug(
                "Render timing: clear={:.1f}ms terrain={:.1f}ms buildings={:.1f}ms "
                "resources={:.1f}ms units={:.1f}ms hud+panel={:.1f}ms submit={:.1f}ms "
                "total={:.1f}ms",
                (t1 - t0) * 1000, (t2 - t1) * 1000, (t3 - t2) * 1000,
                (t4 - t3) * 1000, (t5 - t4) * 1000, (t6 - t5) * 1000,
                (t7 - t6) * 1000, (t7 - t0) * 1000,
            )
            self._render_log_time = 0.0

    def _render_weapon_on_ground(self, buffer: np.ndarray, weapon: WeaponInstance) -> None:
        """渲染地面上的武器."""
        from src.render.sprite import draw_circle, draw_line, draw_text
        sx, sy = weapon.drop_x, weapon.drop_y
        spec = weapon.spec
        color = (200, 200, 200, 180)

        if spec.name == "长矛":
            draw_line(buffer, sx - 8, sy, sx + 8, sy, color, 2)
        elif spec.name == "剑":
            draw_line(buffer, sx - 5, sy, sx + 5, sy, color, 2)
            draw_line(buffer, sx + 1, sy - 3, sx + 1, sy + 3, color, 1)
        elif spec.name == "盾":
            draw_circle(buffer, sx, sy, 5, color, 2)

        draw_text(buffer, sx - 4, sy - 10, spec.name[0], (255, 255, 255, 150), 8)

    def _render_hud(self, buffer: np.ndarray) -> None:
        """渲染简单的HUD信息（中文）."""
        overlay = getattr(self, 'overlay', None)
        if overlay is None:
            return

        mins = int(self.elapsed_time // 60)
        secs = int(self.elapsed_time % 60)
        overlay.draw_text(10, 10, f"运行: {mins:02d}:{secs:02d}", (255, 255, 255, 200), 12.0)

        y_offset = 30
        for faction in self.factions:
            strategy_cn = {
                "expand": "扩张",
                "rush": "突击",
                "defense": "防御",
                "tech": "科技",
            }.get(faction.current_strategy, faction.current_strategy)
            info = f"{faction.name}: 存活={faction.alive_count} 木={faction.wood} 矿={faction.ore} [{strategy_cn}]"
            r, g, b, _ = Unit._hex_to_rgba(faction.color_hex)
            overlay.draw_text(10, y_offset, info, (r, g, b, 220), 12.0)
            y_offset += 18

    def _render_weapon_on_ground_overlay(self, overlay: object, weapon: WeaponInstance) -> None:
        """使用overlay直接API渲染地面上的武器."""
        sx, sy = int(round(weapon.drop_x)), int(round(weapon.drop_y))
        spec = weapon.spec
        color = (200, 200, 200, 180)

        if spec.name == "长矛":
            overlay.draw_line(sx - 8, sy, sx + 8, sy, color, 2)
        elif spec.name == "剑":
            overlay.draw_line(sx - 5, sy, sx + 5, sy, color, 2)
            overlay.draw_line(sx + 1, sy - 3, sx + 1, sy + 3, color, 1)
        elif spec.name == "盾":
            overlay.draw_circle(sx, sy, 5, color, 2)

        overlay.draw_text(sx - 4, sy - 10, spec.name[0], (255, 255, 255, 150), 8.0)

    def _render_hud_overlay(self, overlay: object) -> None:
        """使用overlay直接API渲染HUD信息（中文）."""
        mins = int(self.elapsed_time // 60)
        secs = int(self.elapsed_time % 60)
        overlay.draw_text(10, 10, f"运行: {mins:02d}:{secs:02d}", (255, 255, 255, 200), 12.0)

        y_offset = 30
        for faction in self.factions:
            strategy_cn = {
                "expand": "扩张",
                "rush": "突击",
                "defense": "防御",
                "tech": "科技",
            }.get(faction.current_strategy, faction.current_strategy)
            info = f"{faction.name}: 存活={faction.alive_count} 木={faction.wood} 矿={faction.ore} [{strategy_cn}]"
            r, g, b, _ = Unit._hex_to_rgba(faction.color_hex)
            overlay.draw_text(10, y_offset, info, (r, g, b, 220), 12.0)
            y_offset += 18

    def get_total_unit_count(self) -> int:
        """获取存活单位总数."""
        return sum(1 for u in self.units if u.alive)

    def handle_mouse_down(self, mx: int, my: int) -> None:
        """处理鼠标点击 (面板拖拽)."""
        if self._panel is not None:
            self._panel.handle_mouse_down(mx, my)

    def handle_mouse_move(self, mx: int, my: int) -> None:
        """处理鼠标移动 (面板拖拽)."""
        if self._panel is not None:
            self._panel.handle_mouse_move(mx, my)

    def handle_mouse_up(self) -> None:
        """处理鼠标释放."""
        if self._panel is not None:
            self._panel.handle_mouse_up()
