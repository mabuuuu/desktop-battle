"""Desktop Battle - 伤害计算.

包含伤害随机浮动、护盾减伤、武器伤害计算。
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entity.unit import Unit


def calculate_damage(
    attacker: Unit,
    defender: Unit,
    base_damage: float,
    damage_multiplier: float = 1.0,
) -> float:
    """计算攻击造成的实际伤害.

    算法:
    1. 基础伤害 = base_damage * random(0.8, 1.2)
    2. 武器伤害加成
    3. 盾减伤: damage * (1.0 - damage_reduction)
    4. 应用伤害倍率

    Args:
        attacker: 攻击方单位
        defender: 防御方单位
        base_damage: 基础伤害值
        damage_multiplier: 伤害倍率 (用于全局难度调整)

    Returns:
        实际伤害值
    """
    # 1. 随机浮动: ±20%
    rolled = base_damage * random.uniform(0.8, 1.2)

    # 2. 武器加成 (如果攻击者装备了武器)
    weapon_damage = 0.0
    damage_reduction = 0.0
    if attacker.weapon is not None:
        try:
            weapon_damage = attacker.weapon.damage  # type: ignore[union-attr]
            damage_reduction = attacker.weapon.damage_reduction  # type: ignore[union-attr]
        except AttributeError:
            pass

    # 攻击者的武器伤害 (武器本身的基础伤害已经含在 base_damage 中)
    # 此处 weapon_damage 作为附加加成
    total_damage = rolled + weapon_damage * 0.3

    # 3. 防御方盾减伤
    defender_reduction = 0.0
    if defender.weapon is not None:
        try:
            defender_reduction = defender.weapon.damage_reduction  # type: ignore[union-attr]
        except AttributeError:
            pass

    # 取攻守双方减伤率较大者
    effective_reduction = max(damage_reduction, defender_reduction)
    if effective_reduction > 0.0:
        total_damage *= (1.0 - effective_reduction)

    # 4. 伤害倍率
    total_damage *= damage_multiplier

    # 确保最小伤害
    total_damage = max(0.5, total_damage)

    return round(total_damage, 1)


def calculate_shield_reduction(damage: float, shield_reduction: float = 0.4) -> float:
    """计算盾牌减伤后的伤害.

    Args:
        damage: 原始伤害
        shield_reduction: 减伤率 (默认40%)

    Returns:
        减伤后伤害 = damage * (1 - shield_reduction)
    """
    return damage * (1.0 - shield_reduction)


def get_knockback_impulse(
    attacker: Unit,
    base_knockback: float = 50.0,
) -> tuple[float, float]:
    """计算击退冲量.

    Args:
        attacker: 攻击方 (确定方向)
        base_knockback: 基础击退力

    Returns:
        (impulse_x, impulse_y) 击退冲量向量
    """
    direction = 1.0 if attacker.facing_right else -1.0

    # 武器提供额外击退
    if attacker.weapon is not None:
        try:
            base_knockback = attacker.weapon.knockback  # type: ignore[union-attr]
        except AttributeError:
            pass

    return (direction * base_knockback, 100.0)
