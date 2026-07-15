"""Desktop Battle - 攻击执行.

近战攻击逻辑: 范围检测、冷却管理、伤害施加、击退效果。
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.world import World
    from src.entity.unit import Unit


def execute_melee_attack(attacker: Unit, defender: Unit, world: World) -> bool:
    """执行近战攻击.

    1. 检查攻击范围
    2. 计算伤害
    3. 施加伤害到防御者
    4. 施加击退冲量
    5. 设置攻击冷却

    Args:
        attacker: 攻击方
        defender: 防御方
        world: 世界引用 (用于获取坐标转换)

    Returns:
        攻击是否成功
    """
    if not attacker.alive or not defender.alive:
        return False

    # 检查攻击范围
    sx, sy = attacker.screen_position(world.screen_height)
    dx, dy = defender.screen_position(world.screen_height)

    # 武器攻击范围
    attack_range = 20.0  # 徒手
    base_damage = 2.5  # 徒手伤害 (取随机前均值)
    if attacker.weapon is not None:
        try:
            attack_range = attacker.weapon.attack_range  # type: ignore[union-attr]
            base_damage = attacker.weapon.damage  # type: ignore[union-attr]
        except AttributeError:
            pass

    dist = math.sqrt((sx - dx) ** 2 + (sy - dy) ** 2)
    if dist > attack_range:
        return False

    # 伤害计算
    from src.combat.damage import calculate_damage, get_knockback_impulse

    damage = calculate_damage(attacker, defender, base_damage)
    defender.take_damage(damage)

    # 击退冲量
    knockback = get_knockback_impulse(attacker)
    if defender.body is not None:
        defender.body.apply_impulse_at_world_point(knockback, defender.body.position)

    # 设置攻击冷却
    if attacker.weapon is not None:
        try:
            attacker.attack_cooldown = attacker.weapon.attack_speed  # type: ignore[union-attr]
        except AttributeError:
            attacker.attack_cooldown = 1.5
    else:
        attacker.attack_cooldown = 1.5

    # 如果击杀了目标，清除战斗目标
    if not defender.alive:
        attacker.combat_target_id = None

    return True


def is_in_attack_range(
    attacker: Unit,
    target_x: float,
    target_y: float,
    screen_height: int,
) -> bool:
    """检查目标是否在攻击范围内.

    Args:
        attacker: 攻击方
        target_x: 目标屏幕X
        target_y: 目标屏幕Y
        screen_height: 屏幕高度

    Returns:
        是否在范围内
    """
    sx, sy = attacker.screen_position(screen_height)
    attack_range = 20.0
    if attacker.weapon is not None:
        try:
            attack_range = attacker.weapon.attack_range  # type: ignore[union-attr]
        except AttributeError:
            pass

    dist = math.sqrt((sx - target_x) ** 2 + (sy - target_y) ** 2)
    return dist <= attack_range


def can_unit_attack(unit: Unit) -> bool:
    """检查单位是否可以攻击 (冷却完毕)."""
    return unit.alive and unit.attack_cooldown <= 0.0


def update_attack_cooldown(unit: Unit, dt: float) -> None:
    """更新攻击冷却计时器."""
    if unit.attack_cooldown > 0.0:
        unit.attack_cooldown = max(0.0, unit.attack_cooldown - dt)


def find_nearest_enemy_in_range(
    unit: Unit,
    world: World,
    max_range: float | None = None,
) -> Unit | None:
    """在感知范围内找到最近的敌方单位.

    Args:
        unit: 当前单位
        world: 世界引用
        max_range: 最大搜索范围 (默认使用 unit.perception_range)

    Returns:
        最近的敌方单位或 None
    """
    if max_range is None:
        max_range = unit.perception_range

    sx, sy = unit.screen_position(world.screen_height)
    nearest = None
    nearest_dist = float("inf")

    for other in world.units:
        if not other.alive or other.faction_name == unit.faction_name:
            continue
        ox, oy = other.screen_position(world.screen_height)
        d = math.sqrt((sx - ox) ** 2 + (sy - oy) ** 2)
        if d < max_range and d < nearest_dist:
            nearest_dist = d
            nearest = other

    return nearest
