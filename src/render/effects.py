"""Desktop Battle - 视觉特效渲染.

攻击闪光、死亡粒子、受伤闪烁等视觉特效，全部在 numpy RGBA 缓冲上绘制。
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass


def draw_attack_flash(
    buffer: np.ndarray,
    x: float,
    y: float,
    color: tuple[int, int, int, int] = (255, 255, 200, 200),
    size: int = 12,
    alpha: int = 200,
) -> None:
    """在攻击命中位置绘制闪光效果.

    Args:
        buffer: numpy RGBA 缓冲
        x: 中心X (屏幕坐标)
        y: 中心Y (屏幕坐标)
        color: 闪光颜色
        size: 闪光大小
        alpha: 透明度
    """
    from src.render.sprite import draw_circle
    flash_color = (color[0], color[1], color[2], alpha)
    draw_circle(buffer, x, y, size, flash_color, 1)


def draw_hit_spark(
    buffer: np.ndarray,
    x: float,
    y: float,
    spark_count: int = 4,
) -> None:
    """绘制命中火花粒子.

    Args:
        buffer: numpy RGBA 缓冲
        x: 命中点X
        y: 命中点Y
        spark_count: 火花数量
    """
    from src.render.sprite import draw_line

    spark_colors = [
        (255, 220, 100, 220),
        (255, 180, 60, 200),
        (255, 255, 160, 180),
    ]

    for _ in range(spark_count):
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(4, 10)
        ex = x + math.cos(angle) * dist
        ey = y + math.sin(angle) * dist
        color = random.choice(spark_colors)
        draw_line(buffer, x, y, ex, ey, color, 1)


def draw_death_particles(
    buffer: np.ndarray,
    x: float,
    y: float,
    faction_color: tuple[int, int, int, int],
    particle_count: int = 10,
    frame: int = 0,
) -> None:
    """绘制死亡粒子效果.

    Args:
        buffer: numpy RGBA 缓冲
        x: 死亡位置X
        y: 死亡位置Y
        faction_color: 阵营颜色
        particle_count: 粒子数量
        frame: 动画帧 (用于控制速度和生命周期)
    """
    from src.render.sprite import draw_circle, draw_line

    rng = random.Random(x + y + frame)

    base_color = (
        min(255, faction_color[0] + 60),
        min(255, faction_color[1] + 60),
        min(255, faction_color[2] + 60),
        200,
    )

    for i in range(particle_count):
        angle = rng.uniform(0, math.pi * 2)
        speed = rng.uniform(1.5, 4.0)
        lifetime = 5 + int(i * 0.5)
        life_phase = frame % max(lifetime, 1)

        if life_phase >= lifetime:
            continue

        alpha = int(200 * (1.0 - life_phase / lifetime))
        px = x + math.cos(angle) * speed * life_phase
        py = y + math.sin(angle) * speed * life_phase

        p_color = (base_color[0], base_color[1], base_color[2], alpha)
        p_size = max(1, 3 - life_phase // 2)
        draw_circle(buffer, px, py, p_size, p_color, 0)

    # 中心消散光圈
    ring_radius = 5 + (frame % 15)
    ring_alpha = max(0, 180 - (frame % 15) * 12)
    ring_color = (base_color[0], base_color[1], base_color[2], ring_alpha)
    draw_circle(buffer, x, y, ring_radius, ring_color, 1)


def draw_damage_number(
    buffer: np.ndarray,
    x: float,
    y: float,
    damage: float,
    frame: int = 0,
    color: tuple[int, int, int, int] = (255, 80, 80, 250),
) -> None:
    """绘制浮动伤害数字.

    Args:
        buffer: numpy RGBA 缓冲
        x: 位置X
        y: 位置Y
        damage: 伤害值
        frame: 动画帧
        color: 数字颜色
    """
    from src.render.sprite import draw_text

    # 浮动效果: 向上飘动
    float_y = y - (frame % 20) * 0.8
    float_alpha = max(0, 250 - (frame % 20) * 12)

    text_color = (color[0], color[1], color[2], float_alpha)
    text = f"-{int(damage)}"
    draw_text(buffer, x - 6, float_y, text, text_color, font_size=9)


class EffectManager:
    """视觉特效管理器.

    管理攻击闪光、粒子、伤害数字的队列和生命周期。
    """

    def __init__(self, max_effects: int = 50) -> None:
        self._attack_flashes: list[AttackFlash] = []
        self._death_particles: list[DeathParticle] = []
        self._damage_numbers: list[DamageNumber] = []
        self._max_effects = max_effects

    def add_attack_flash(self, x: float, y: float) -> None:
        """添加攻击闪光."""
        if len(self._attack_flashes) < self._max_effects:
            self._attack_flashes.append(AttackFlash(x, y))

    def add_death_particles(
        self, x: float, y: float, faction_color: tuple[int, int, int, int]
    ) -> None:
        """添加死亡粒子."""
        if len(self._death_particles) < self._max_effects:
            self._death_particles.append(DeathParticle(x, y, faction_color))

    def add_damage_number(self, x: float, y: float, damage: float) -> None:
        """添加浮动伤害数字."""
        if len(self._damage_numbers) < self._max_effects:
            self._damage_numbers.append(DamageNumber(x, y, damage))

    def update_and_render(self, buffer: np.ndarray, frame: int) -> None:
        """更新所有特效并渲染.

        Args:
            buffer: numpy RGBA 渲染缓冲
            frame: 当前帧计数
        """
        # 攻击闪光
        for flash in list(self._attack_flashes):
            flash.life -= 1
            if flash.life <= 0:
                self._attack_flashes.remove(flash)
            else:
                draw_attack_flash(buffer, flash.x, flash.y, size=8 + flash.life)
                draw_hit_spark(buffer, flash.x, flash.y, spark_count=3)

        # 死亡粒子
        for particle in list(self._death_particles):
            particle.life -= 1
            if particle.life <= 0:
                self._death_particles.remove(particle)
            else:
                draw_death_particles(
                    buffer, particle.x, particle.y, particle.color,
                    particle_count=8, frame=particle.life,
                )

        # 伤害数字
        for dn in list(self._damage_numbers):
            dn.life -= 1
            if dn.life <= 0:
                self._damage_numbers.remove(dn)
            else:
                draw_damage_number(buffer, dn.x, dn.y, dn.damage, frame=20 - dn.life)


class AttackFlash:
    """攻击闪光数据."""
    def __init__(self, x: float, y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.life: int = 6  # 帧


class DeathParticle:
    """死亡粒子数据."""
    def __init__(
        self, x: float, y: float, color: tuple[int, int, int, int]
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.color: tuple[int, int, int, int] = color
        self.life: int = 20  # 帧


class DamageNumber:
    """浮动伤害数字数据."""
    def __init__(self, x: float, y: float, damage: float) -> None:
        self.x: float = x
        self.y: float = y
        self.damage: float = damage
        self.life: int = 20  # 帧
