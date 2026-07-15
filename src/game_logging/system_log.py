"""Desktop Battle - 系统日志记录器.

记录 FPS 统计、窗口扫描、建筑事件、生产/制作系统事件。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from src.entity.building import Building
    from src.entity.faction import Faction


def log_fps(fps: float, unit_count: int, frame_count: int) -> None:
    """记录帧率统计.

    Args:
        fps: 当前FPS
        unit_count: 存活单位数
        frame_count: 总帧数
    """
    logger.bind(channel="system").debug(
        "FPS: {:.0f} | Units: {} | Frame: {}",
        fps,
        unit_count,
        frame_count,
    )


def log_window_scan(window_count: int, scan_time_ms: float) -> None:
    """记录窗口扫描结果.

    Args:
        window_count: 检测到的窗口数
        scan_time_ms: 扫描耗时(毫秒)
    """
    logger.bind(channel="system").debug(
        "WindowScan | {} windows | {:.1f}ms",
        window_count,
        scan_time_ms,
    )


def log_building_created(building: Building, faction: Faction) -> None:
    """记录建筑创建.

    Args:
        building: 新建筑
        faction: 所属阵营
    """
    logger.bind(channel="system").info(
        "Building | {} created {} Lv{} (total buildings: {})",
        faction.name,
        building.building_type,
        building.level,
        len(faction.buildings),
    )


def log_building_destroyed(building: Building, faction: Faction) -> None:
    """记录建筑被摧毁.

    Args:
        building: 被摧毁建筑
        faction: 所属阵营
    """
    logger.bind(channel="system").info(
        "Building | {} destroyed {} Lv{} (remaining: {})",
        faction.name,
        building.building_type,
        building.level,
        len(faction.buildings),
    )


def log_unit_spawned(faction: Faction, unit_id: int) -> None:
    """记录单位生产.

    Args:
        faction: 所属阵营
        unit_id: 新单位ID
    """
    logger.bind(channel="system").info(
        "Spawn | {} unit[{}] (total units: {})",
        faction.name,
        unit_id,
        faction.alive_count,
    )


def log_production_queue(
    building: Building,
    queue_size: int,
    faction_name: str,
) -> None:
    """记录生产队列状态.

    Args:
        building: 兵营建筑
        queue_size: 队列大小
        faction_name: 阵营名
    """
    logger.bind(channel="system").debug(
        "Production | {} barracks queue: {}/{}",
        faction_name,
        queue_size,
        building.can_produce(),
    )


def log_resource_balance(faction: Faction) -> None:
    """记录阵营资源余额.

    Args:
        faction: 阵营
    """
    logger.bind(channel="system").debug(
        "Resource | {} W={} O={}",
        faction.name,
        faction.wood,
        faction.ore,
    )


def log_game_start(config_info: str) -> None:
    """记录游戏启动信息.

    Args:
        config_info: 配置摘要
    """
    logger.bind(channel="system").info("GameStart | {}", config_info)


def log_game_shutdown(runtime_seconds: float) -> None:
    """记录游戏关闭.

    Args:
        runtime_seconds: 运行时长
    """
    logger.bind(channel="system").info("GameShutdown | Runtime: {:.1f}s", runtime_seconds)


def log_ai_strategy_update(faction_name: str, strategy: str) -> None:
    """记录AI策略更新.

    Args:
        faction_name: 阵营名
        strategy: 新策略名
    """
    logger.bind(channel="system").info(
        "Strategy | {} → {}",
        faction_name,
        strategy,
    )
