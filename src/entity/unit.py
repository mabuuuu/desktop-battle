"""Desktop Battle - 单位实体.

火柴人战士单位：属性、物理体、状态管理、渲染。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import pymunk

from src.desktop.coord import physics_to_screen
from src.physics.body_factory import create_unit_body

if TYPE_CHECKING:
    from src.combat.weapon import WeaponInstance
    from src.core.config import FactionConfig, GameConfig
    from src.render.sprite import hex_to_rgba as _hex_to_rgba


class UnitState(str, Enum):
    """单位行为状态."""

    IDLE = "idle"
    WALKING = "walking"
    MINING = "mining"
    CRAFTING = "crafting"
    FIGHTING = "fighting"
    FLEEING = "fleeing"
    CLIMBING = "climbing"
    BUILDING = "building"
    DYING = "dying"
    CARRYING = "carrying"
    ARGUING = "arguing"
    PATROLLING = "patrolling"  # 巡逻
    SCOUTING = "scouting"      # 侦察


class UnitRole(str, Enum):
    """单位职责角色."""

    GATHERER = "gatherer"    # 生产者: 采集+运送
    BUILDER = "builder"      # 建造者: 建造+制作
    SOLDIER = "soldier"      # 战士: 巡逻+战斗
    SCOUT = "scout"          # 侦察: 探索+预警
    IDLE = "idle"            # 未分配


@dataclass
class Unit:
    """桌面火柴人单位实体.

    拥有 pymunk 物理体、HP、状态、阵营信息等。
    """

    unit_id: int
    faction_name: str
    faction_color_hex: str
    faction_secondary_hex: str
    config: GameConfig
    faction_cfg: object  # FactionConfig

    # ── 物理体 ──
    body: pymunk.Body | None = None
    shape: pymunk.Circle | None = None
    on_ground: bool = False

    # ── 属性 ──
    hp: float = 1000.0
    max_hp: float = 1000.0
    move_speed: float = 60.0
    perception_range: float = 100.0

    # ── 状态 ──
    state: UnitState = UnitState.IDLE
    prev_state: UnitState = UnitState.IDLE
    state_blend: float = 0.0  # 状态过渡混合因子 (0=旧状态, 1=新状态)
    anim_time: float = 0.0  # 动画时间(秒)，替代anim_frame
    anim_frame: int = 0
    facing_right: bool = True
    alive: bool = True
    role: UnitRole = UnitRole.IDLE  # 当前职责

    # ── 目标 ──
    target_id: int | None = None
    target_type: str | None = None  # "unit", "resource", "building", "weapon"

    # ── 采集 ──
    carrying_wood: int = 0
    carrying_ore: int = 0

    # ── 武器 ──
    weapon: object | None = None  # WeaponInstance (避免循环导入)

    # ── 建造 ──
    build_progress: float = 0.0
    build_target: object | None = None

    # ── 战斗 ──
    attack_cooldown: float = 0.0
    combat_target_id: int | None = None

    # ── 渲染缓存 ──
    _rgba_color: tuple[int, int, int, int] = field(default=(255, 68, 68, 255), repr=False)
    _rgba_secondary: tuple[int, int, int, int] = field(default=(255, 136, 102, 255), repr=False)

    def __post_init__(self) -> None:
        self._rgba_color = self._hex_to_rgba(self.faction_color_hex)
        self._rgba_secondary = self._hex_to_rgba(self.faction_secondary_hex)

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
        hex_str = hex_color.lstrip("#")
        return (
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
            alpha,
        )

    def init_physics(self, phys_x: float, phys_y: float) -> None:
        """初始化单位物理体."""
        body, shape = create_unit_body(
            x=phys_x,
            y=phys_y,
            mass=self.config.unit_mass,
            radius=self.config.unit_radius,
            friction=self.config.unit_friction,
            elasticity=self.config.unit_elasticity,
        )
        self.body = body
        self.shape = shape
        # 将 unit 引用附加到 shape 上以便碰撞回调使用
        shape.data = self

    def screen_position(self, screen_height: int) -> tuple[float, float]:
        """获取单位在屏幕坐标系中的位置 (Y轴向下)."""
        if self.body is None:
            return (0.0, 0.0)
        return physics_to_screen(self.body.position.x, self.body.position.y, screen_height)

    def move_toward(self, target_x: float) -> None:
        """向目标X坐标移动（施加水平力）."""
        if self.body is None or self.body.body_type != pymunk.Body.DYNAMIC:
            return
        dx = target_x - self.body.position.x
        direction = 1.0 if dx > 0 else -1.0

        # 更新朝向
        self.facing_right = dx > 0

        # 应用速度倍率
        effective_speed = self.move_speed * self.config.move_speed_multiplier

        # 施加力（补偿阻尼）
        force_magnitude = effective_speed * 10.0
        self.body.apply_force_at_local_point((direction * force_magnitude, 0.0), (0.0, 0.0))

        # 限制最大速度
        vx = self.body.velocity.x
        if abs(vx) > effective_speed:
            self.body.velocity = (direction * effective_speed, self.body.velocity.y)

        if self.state not in (UnitState.FIGHTING, UnitState.CLIMBING,
                              UnitState.DYING, UnitState.MINING,
                              UnitState.BUILDING, UnitState.CRAFTING):
            self.state = UnitState.WALKING

    def jump(self, impulse: float = 300.0) -> None:
        """跳跃冲量."""
        if self.body is None or not self.on_ground:
            return
        self.body.apply_impulse_at_local_point((0.0, impulse), (0.0, 0.0))
        self.on_ground = False

    def take_damage(self, damage: float) -> float:
        """受到伤害，返回实际伤害值."""
        self.hp = max(0.0, self.hp - damage)
        if self.hp <= 0.0:
            self.alive = False
            self.state = UnitState.DYING
        return damage

    def equip_weapon(self, weapon: object) -> None:
        """装备武器."""
        self.weapon = weapon

    def unequip_weapon(self) -> object | None:
        """卸下武器并返回."""
        w = self.weapon
        self.weapon = None
        return w

    @property
    def total_carried(self) -> int:
        """总携带资源量."""
        return self.carrying_wood + self.carrying_ore

    @property
    def carrying_full(self) -> bool:
        """是否携带已满."""
        return self.total_carried >= self.config.unit_carry_capacity

    def add_carry(self, wood: int = 0, ore: int = 0) -> None:
        """添加携带资源."""
        capacity = self.config.unit_carry_capacity
        remaining = capacity - self.total_carried
        total_add = min(wood + ore, remaining)
        if total_add <= 0:
            return
        if wood + ore > 0:
            ratio = total_add / (wood + ore)
            self.carrying_wood += int(wood * ratio)
            self.carrying_ore += int(ore * ratio)

    def clear_carry(self) -> tuple[int, int]:
        """清空并返回携带资源."""
        w, o = self.carrying_wood, self.carrying_ore
        self.carrying_wood = 0
        self.carrying_ore = 0
        return (w, o)

    def get_weapon_visual(self) -> tuple[str, int] | None:
        """获取武器绘制信息 (类型名, 视觉长度)."""
        if self.weapon is None:
            return None
        # 假设 weapon 对象有 spec 属性
        try:
            spec = self.weapon.spec  # type: ignore[union-attr]
            return (spec.name.lower(), spec.visual_length)
        except AttributeError:
            return None

    def update_animation(self) -> None:
        """更新动画帧（时间驱动）."""
        self.anim_time += 1.0 / 60.0  # 假设60fps
        self.anim_frame = int(self.anim_time * 60.0) % 10000  # 兼容旧代码

        # 状态过渡混合
        if self.state != self.prev_state:
            self.state_blend = 0.0
            self.prev_state = self.state
        elif self.state_blend < 1.0:
            self.state_blend = min(1.0, self.state_blend + 0.15)  # ~7帧过渡

    def render(
        self,
        buffer: np.ndarray,
        screen_height: int,
    ) -> None:
        """在 numpy RGBA 缓冲上渲染火柴人."""
        if not self.alive:
            return
        sx, sy = self.screen_position(screen_height)
        # 身体中心在屏幕上的位置 (物理体中心)
        from src.render.sprite import draw_health_bar, draw_stickman

        # 绘制血条
        hp_ratio = self.hp / self.max_hp
        bar_width = 10
        bar_y = sy - self.config.stickman_height - 4
        draw_health_bar(
            buffer,
            sx - bar_width / 2,
            bar_y,
            bar_width,
            2,
            self.hp,
            self.max_hp,
            self._rgba_color,
            (40, 40, 40, 180),
        )

        # 绘制火柴人
        weapon_vis = self.get_weapon_visual()
        draw_stickman(
            buffer,
            sx,
            sy,
            self._rgba_color,
            self._rgba_secondary,
            line_width=self.config.stickman_line_width,
            head_radius=self.config.stickman_head_radius,
            state=self.state.value,
            anim_frame=self.anim_frame,
            weapon_visual=weapon_vis,
            facing_right=self.facing_right,
        )

        # 如果正在携带资源，绘制头顶的资源标记
        if self.carrying_wood > 0 or self.carrying_ore > 0:
            from src.render.sprite import draw_circle
            mark_y = sy - self.config.stickman_height - 2
            if self.carrying_wood > 0:
                draw_circle(buffer, sx - 1.5, mark_y, 1.5, (68, 204, 68, 200), 0)
            if self.carrying_ore > 0:
                draw_circle(buffer, sx + 1.5, mark_y, 1.5, (204, 170, 68, 200), 0)
