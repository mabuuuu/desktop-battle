"""Desktop Battle - 错误日志记录器.

记录异常、物理引擎错误、崩溃信息。永久保留，不自动删除。
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass


def log_exception(
    exc: Exception,
    context: str = "",
    fatal: bool = False,
) -> None:
    """记录异常.

    Args:
        exc: 异常对象
        context: 上下文描述
        fatal: 是否为致命错误
    """
    level = "CRITICAL" if fatal else "ERROR"
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.bind(channel="system").log(
        level,
        "Exception [{}] {}: {}\n{}",
        "FATAL" if fatal else "ERROR",
        context,
        exc,
        "".join(tb[-3:]),  # 最后3帧
    )


def log_physics_error(
    message: str,
    details: str = "",
) -> None:
    """记录物理引擎错误.

    Args:
        message: 错误描述
        details: 详细信息
    """
    logger.bind(channel="system").error(
        "PhysicsError | {} {}",
        message,
        f"({details})" if details else "",
    )


def log_collision_error(
    entity_type: str,
    entity_id: int,
    message: str,
) -> None:
    """记录碰撞处理错误.

    Args:
        entity_type: 实体类型
        entity_id: 实体ID
        message: 错误描述
    """
    logger.bind(channel="system").error(
        "CollisionError | {}[{}]: {}",
        entity_type,
        entity_id,
        message,
    )


def log_ai_error(
    faction_name: str,
    error_message: str,
    retry_count: int = 0,
) -> None:
    """记录AI调用错误.

    Args:
        faction_name: 阵营名
        error_message: 错误描述
        retry_count: 重试次数
    """
    logger.bind(channel="system").error(
        "AI_Error | {} retry={}: {}",
        faction_name,
        retry_count,
        error_message,
    )


def log_behavior_error(
    unit_id: int,
    node_name: str,
    error_message: str,
) -> None:
    """记录行为树节点错误.

    Args:
        unit_id: 单位ID
        node_name: 节点名
        error_message: 错误描述
    """
    logger.bind(channel="system").error(
        "BT_Error | Unit[{}] node[{}]: {}",
        unit_id,
        node_name,
        error_message,
    )


def log_resource_error(
    faction_name: str,
    resource_type: str,
    message: str,
) -> None:
    """记录资源系统错误.

    Args:
        faction_name: 阵营名
        resource_type: 资源类型
        message: 错误描述
    """
    logger.bind(channel="system").error(
        "ResourceError | {} {}: {}",
        faction_name,
        resource_type,
        message,
    )


def log_shutdown_error(exc: Exception) -> None:
    """记录关闭时的清理错误.

    Args:
        exc: 异常
    """
    logger.bind(channel="system").error(
        "ShutdownError | Cleanup failed: {}",
        exc,
    )
