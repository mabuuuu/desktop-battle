"""Desktop Battle - 日志管理器.

基于 loguru 实现三通道日志:
- system: 系统日志 (FPS, 窗口扫描, 建筑事件)
- behavior: 行为日志 (状态转换, 攻击命中, 死亡)
- error: 错误日志 (异常, 物理错误, 永久保留)

轮转策略: 每天轮转, 保留30天, 压缩旧日志。
"""

from __future__ import annotations

import os
import sys

from loguru import logger


class LogManager:
    """游戏日志管理器.

    三通道日志系统, 使用 loguru 的 sink 机制分别写入不同文件。
    """

    LOG_DIR: str = "logs"

    def __init__(self, log_dir: str | None = None) -> None:
        self._log_dir: str = log_dir or self.LOG_DIR
        self._initialized: bool = False

    def setup(self) -> None:
        """初始化所有日志通道."""
        if self._initialized:
            return

        # 确保日志目录存在
        os.makedirs(self._log_dir, exist_ok=True)

        # 移除默认 handler
        logger.remove()

        # 保留控制台输出 (用于调试)
        logger.add(
            sys.stderr,
            format=(
                "<level>{time:HH:mm:ss.SSS}</level> "
                "|<level>{level:<7}</level>| "
                "{message}"
            ),
            level="DEBUG",
            colorize=True,
        )

        # ── 系统日志 ──
        logger.add(
            os.path.join(self._log_dir, "system_{time:YYYY-MM-DD}.log"),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="00:00",  # 每天午夜轮转
            retention="30 days",  # 保留30天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            filter=self._system_filter,
        )

        # ── 行为日志 ──
        logger.add(
            os.path.join(self._log_dir, "behavior_{time:YYYY-MM-DD}.log"),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {message}",
            level="DEBUG",
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            filter=self._behavior_filter,
        )

        # ── 错误日志 (永久保留) ──
        logger.add(
            os.path.join(self._log_dir, "error.log"),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="10 MB",  # 超过10MB轮转
            retention=0,  # 不自动删除
            encoding="utf-8",
            filter=self._error_filter,
        )

        self._initialized = True

    @staticmethod
    def _system_filter(record: dict) -> bool:
        """系统日志过滤器: system.* 或非 behavior/error 类消息."""
        extra = record.get("extra", {})
        channel = extra.get("channel", "system")
        return channel == "system"

    @staticmethod
    def _behavior_filter(record: dict) -> bool:
        """行为日志过滤器: behavior.* 消息."""
        extra = record.get("extra", {})
        channel = extra.get("channel", "behavior")
        return channel == "behavior"

    @staticmethod
    def _error_filter(record: dict) -> bool:
        """错误日志过滤器: ERROR 级别以上."""
        return record["level"].name in ("ERROR", "CRITICAL")


# 全局实例
_log_manager: LogManager | None = None


def get_log_manager(log_dir: str | None = None) -> LogManager:
    """获取全局日志管理器 (单例)."""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager(log_dir)
        _log_manager.setup()
    return _log_manager


def init_logging(log_dir: str | None = None) -> LogManager:
    """初始化日志系统."""
    mgr = get_log_manager(log_dir)
    mgr.setup()
    return mgr
