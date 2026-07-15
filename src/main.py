"""Desktop Battle - 桌面火柴人大乱斗 入口.

启动透明覆盖层窗口、游戏主循环、系统托盘。
集成所有系统: 行为树AI, 战斗, 攀爬, 日志, 面板, AI策略。

    运行方式:
        cd D:/projects/desktop-battle
        python -m src.main
"""

from __future__ import annotations

import sys
import threading
import traceback

from loguru import logger

from src.core.config import GameConfig
from src.core.game_loop import GameLoop
from src.core.world import World
from src.render.overlay import TransparentOverlay


def setup_logging() -> None:
    """初始化控制台日志 (文件日志由 game_logging 管理)."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{time:HH:mm:ss.SSS}</level> | <level>{level:<7}</level> | {message}",
        level="DEBUG",
    )


def main() -> None:
    """程序入口."""
    setup_logging()
    logger.info("Desktop Battle - Starting...")

    # 加载设置
    from src.ui.settings import SettingsManager
    settings_mgr = SettingsManager.get_instance()
    settings_mgr.load()

    # 加载配置
    try:
        config = GameConfig()
        # 应用运行时设置
        config.game_speed = settings_mgr.settings.game_speed
        if settings_mgr.settings.ai_enabled:
            config.ai.enabled = True
            config.ai.api_key = settings_mgr.settings.ai_api_key
            config.ai.api_url = settings_mgr.settings.ai_api_url
            config.ai.model = settings_mgr.settings.ai_model
            config.ai.strategy_interval = settings_mgr.settings.ai_interval
        config.gravity = settings_mgr.settings.gravity
    except Exception as e:
        logger.error(f"Config error: {e}")
        return

    # 创建透明覆盖层
    overlay: TransparentOverlay | None = None
    game_loop: GameLoop | None = None

    try:
        overlay = TransparentOverlay()
        logger.info("Overlay created: {}x{}", overlay.width, overlay.height)

        # 初始化游戏世界
        world = World(config, overlay)
        world.set_damage_multiplier(settings_mgr.settings.damage_multiplier)
        world.initialize()
        logger.info("World initialized: {} factions, {} units",
                     len(world.factions), len(world.units))

        # 创建主循环
        game_loop = GameLoop(config, overlay)
        game_loop.world = world
        game_loop.physics_engine = world.physics

        # 启动系统托盘 (独立线程)
        from src.ui.tray import TrayManager
        tray = TrayManager(game_loop, panel=world.panel)
        tray.start()
        logger.info("System tray started")

        # 启动覆盖层渲染线程
        overlay.start()
        logger.info("Overlay render thread started")

        # 初始化日志系统
        try:
            from src.game_logging.logger import init_logging
            init_logging()
        except Exception:
            pass

        logger.info(
            "Game starting | Factions: {} | AI: {} | Damage: {:.1f}x",
            len(world.factions),
            "enabled" if config.ai.enabled else "disabled",
            settings_mgr.settings.damage_multiplier,
        )

        # 启动主循环 (阻塞)
        game_loop.start()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        try:
            from src.game_logging.error_log import log_exception
            log_exception(e, "main crash", fatal=True)
        except Exception:
            pass
    finally:
        # 保存设置
        try:
            settings_mgr.save()
        except Exception:
            pass

        # 清理
        try:
            tray.stop()
        except Exception:
            pass
        if overlay is not None:
            overlay.stop()
        if game_loop is not None:
            game_loop.stop()
        logger.info("Desktop Battle - Shutdown complete")


if __name__ == "__main__":
    main()
