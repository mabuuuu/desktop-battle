"""Desktop Battle - AI 策略日志.

记录 AI 策略请求/响应、降级事件、策略切换。
输出到 logs/strategy/ 目录。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from loguru import logger


_STRATEGY_LOG_DIR: str = os.path.join("logs", "strategy")


def _ensure_log_dir() -> None:
    """确保策略日志目录存在."""
    os.makedirs(_STRATEGY_LOG_DIR, exist_ok=True)


def log_strategy_request(
    faction_name: str,
    prompt: str,
) -> None:
    """记录 AI 策略请求.

    Args:
        faction_name: 阵营名
        prompt: 请求内容
    """
    _ensure_log_dir()

    logger.bind(channel="system").info(
        "AI_Request | {} | {} chars",
        faction_name,
        len(prompt),
    )

    # 写入详细日志文件
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(_STRATEGY_LOG_DIR, f"request_{faction_name}_{timestamp}.json")
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({
                "faction": faction_name,
                "timestamp": timestamp,
                "prompt": prompt,
            }, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def log_strategy_response(
    faction_name: str,
    strategy: dict[str, Any],
) -> None:
    """记录 AI 策略响应.

    Args:
        faction_name: 阵营名
        strategy: AI 返回的策略 JSON
    """
    _ensure_log_dir()

    strat_type = strategy.get("strategy", "unknown")
    logger.bind(channel="system").info(
        "AI_Response | {} | strategy={} | json_size={}",
        faction_name,
        strat_type,
        len(json.dumps(strategy)),
    )

    # 写入详细日志文件
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(_STRATEGY_LOG_DIR, f"response_{faction_name}_{timestamp}.json")
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({
                "faction": faction_name,
                "timestamp": timestamp,
                "strategy": strategy,
            }, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def log_fallback(
    faction_name: str,
    reason: str,
) -> None:
    """记录 AI 降级事件.

    Args:
        faction_name: 阵营名
        reason: 降级原因
    """
    logger.bind(channel="system").warning(
        "AI_Fallback | {} | reason={}",
        faction_name,
        reason,
    )

    _ensure_log_dir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(_STRATEGY_LOG_DIR, f"fallback_{faction_name}_{timestamp}.txt")
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Faction: {faction_name}\n")
            f.write(f"Time: {timestamp}\n")
            f.write(f"Reason: {reason}\n")
    except OSError:
        pass


def log_strategy_switch(
    faction_name: str,
    old_strategy: str,
    new_strategy: str,
) -> None:
    """记录策略切换.

    Args:
        faction_name: 阵营名
        old_strategy: 旧策略
        new_strategy: 新策略
    """
    logger.bind(channel="system").info(
        "Strategy_Switch | {} {} → {}",
        faction_name,
        old_strategy,
        new_strategy,
    )
