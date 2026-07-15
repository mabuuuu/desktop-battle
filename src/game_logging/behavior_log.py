"""Desktop Battle - 行为日志记录器.

记录单位状态转换、攻击命中、死亡事件、采集/建造/制作行为。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from src.entity.unit import Unit


# 绑定的 channel 标识 (通过 loguru 的 extra 机制)
_BEHAVIOR_EXTRA: dict[str, str] = {"channel": "behavior"}


def log_state_change(
    unit: Unit,
    old_state: str,
    new_state: str,
    reason: str = "",
) -> None:
    """记录单位状态转换.

    Args:
        unit: 单位
        old_state: 旧状态
        new_state: 新状态
        reason: 转换原因
    """
    logger.bind(channel="behavior").info(
        "Unit[{}] {}: {} → {} {}",
        unit.unit_id,
        unit.faction_name,
        old_state,
        new_state,
        f"({reason})" if reason else "",
    )


def log_attack_hit(
    attacker: Unit,
    defender: Unit,
    damage: float,
    defender_hp_remaining: float,
) -> None:
    """记录攻击命中.

    Args:
        attacker: 攻击方
        defender: 防御方
        damage: 造成伤害
        defender_hp_remaining: 防御方剩余HP
    """
    weapon = "徒手"
    if attacker.weapon is not None:
        try:
            weapon = attacker.weapon.name  # type: ignore[union-attr]
        except AttributeError:
            pass

    logger.bind(channel="behavior").info(
        "Hit | {}[{}]({}) → {}[{}] dmg={:.1f} hp={:.0f}/{:.0f}",
        attacker.faction_name,
        attacker.unit_id,
        weapon,
        defender.faction_name,
        defender.unit_id,
        damage,
        defender_hp_remaining,
        defender.max_hp,
    )


def log_unit_death(unit: Unit, killer: Unit | None = None) -> None:
    """记录单位死亡.

    Args:
        unit: 死亡单位
        killer: 击杀者 (可能为 None)
    """
    if killer is not None:
        logger.bind(channel="behavior").info(
            "Death | {}[{}] killed by {}[{}]",
            unit.faction_name,
            unit.unit_id,
            killer.faction_name,
            killer.unit_id,
        )
    else:
        logger.bind(channel="behavior").info(
            "Death | {}[{}] died",
            unit.faction_name,
            unit.unit_id,
        )


def log_gather(
    unit: Unit,
    resource_type: str,
    amount: int,
    total_carried: int,
) -> None:
    """记录资源采集.

    Args:
        unit: 采集单位
        resource_type: 资源类型
        amount: 本次采集量
        total_carried: 总携带量
    """
    logger.bind(channel="behavior").debug(
        "Gather | {}[{}] +{} {} (carrying: {}/{})",
        unit.faction_name,
        unit.unit_id,
        amount,
        resource_type,
        total_carried,
        unit.config.unit_carry_capacity,
    )


def log_deposit(
    unit: Unit,
    wood: int,
    ore: int,
) -> None:
    """记录资源存入.

    Args:
        unit: 搬运单位
        wood: 存入木材
        ore: 存入矿石
    """
    logger.bind(channel="behavior").info(
        "Deposit | {}[{}] +W{} +O{}",
        unit.faction_name,
        unit.unit_id,
        wood,
        ore,
    )


def log_build_start(
    unit: Unit,
    building_type: str,
    level: int,
) -> None:
    """记录开始建造.

    Args:
        unit: 建造单位
        building_type: 建筑类型
        level: 建筑等级
    """
    logger.bind(channel="behavior").info(
        "BuildStart | {}[{}] → {} Lv{}",
        unit.faction_name,
        unit.unit_id,
        building_type,
        level,
    )


def log_build_complete(
    unit: Unit,
    building_type: str,
    level: int,
) -> None:
    """记录建造完成.

    Args:
        unit: 建造单位
        building_type: 建筑类型
        level: 建筑等级
    """
    logger.bind(channel="behavior").info(
        "BuildDone | {}[{}] → {} Lv{} completed",
        unit.faction_name,
        unit.unit_id,
        building_type,
        level,
    )


def log_craft_start(
    unit: Unit,
    weapon_name: str,
) -> None:
    """记录开始制作武器.

    Args:
        unit: 制作单位
        weapon_name: 武器名称
    """
    logger.bind(channel="behavior").info(
        "CraftStart | {}[{}] → {}",
        unit.faction_name,
        unit.unit_id,
        weapon_name,
    )


def log_craft_complete(
    unit: Unit,
    weapon_name: str,
) -> None:
    """记录制作完成.

    Args:
        unit: 制作单位
        weapon_name: 武器名称
    """
    logger.bind(channel="behavior").info(
        "CraftDone | {}[{}] → {} crafted",
        unit.faction_name,
        unit.unit_id,
        weapon_name,
    )


def log_weapon_pickup(unit: Unit, weapon_name: str) -> None:
    """记录武器拾取.

    Args:
        unit: 拾取单位
        weapon_name: 武器名称
    """
    logger.bind(channel="behavior").info(
        "Pickup | {}[{}] equipped {}",
        unit.faction_name,
        unit.unit_id,
        weapon_name,
    )


def log_climb_start(unit: Unit) -> None:
    """记录开始攀爬."""
    logger.bind(channel="behavior").debug(
        "ClimbStart | {}[{}]",
        unit.faction_name,
        unit.unit_id,
    )


def log_climb_end(unit: Unit) -> None:
    """记录攀爬结束."""
    logger.bind(channel="behavior").debug(
        "ClimbEnd | {}[{}]",
        unit.faction_name,
        unit.unit_id,
    )


# ── 阵营分裂日志 ──


def log_schism(
    original_name: str,
    rebel_name: str,
    split_count: int,
    remaining_count: int,
) -> None:
    """记录阵营分裂事件."""
    logger.bind(channel="behavior").info(
        "SCHISM | {} → {} | Split: {} units | Remaining: {} units",
        original_name,
        rebel_name,
        split_count,
        remaining_count,
    )


def log_schism_resource_grab(
    rebel_name: str,
    resource_type: str,
    success: bool,
) -> None:
    """记录资源点争夺结果."""
    result = "SUCCESS" if success else "FAILED"
    logger.bind(channel="behavior").info(
        "ResourceGrab | {} | {} | {}",
        rebel_name,
        resource_type,
        result,
    )


def log_conflict_accumulate(
    faction_name: str,
    conflict_score: float,
    alive_count: int,
) -> None:
    """记录矛盾值积累."""
    logger.bind(channel="behavior").debug(
        "ConflictAccumulate | {} | Score: {:.1f}/100 | Units: {}",
        faction_name,
        conflict_score,
        alive_count,
    )


def log_argue(unit_id: int, faction_name: str, conflict: float) -> None:
    """记录争吵事件."""
    logger.bind(channel="behavior").debug(
        "Argue | {}[{}] | Conflict: {:.1f}",
        faction_name,
        unit_id,
        conflict,
    )


def log_skirmish(unit_id: int, faction_name: str, conflict: float) -> None:
    """记录小冲突事件."""
    logger.bind(channel="behavior").debug(
        "Skirmish | {}[{}] | Conflict: {:.1f}",
        faction_name,
        unit_id,
        conflict,
    )
