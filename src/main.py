"""Desktop Battle - 桌面火柴人大乱斗 入口.

启动透明覆盖层窗口、游戏主循环、系统托盘。

运行方式:
    cd D:\projects\desktop-battle
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
from src.ui.tray import TrayManager


def setup_logging() -> None:
    """初始化日志系统."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{time:HH:mm:ss} | {level:<7} | {message}</level>",
        level="DEBUG",
    )


def main() -> None:
    """程序入口."""
    setup_logging()
    logger.info("Desktop Battle - Starting...")

    # 加载配置
    try:
        config = GameConfig()
    except Exception as e:
        logger.error(f"Config error: {e}")
        return

    # 创建透明覆盖层
    overlay: TransparentOverlay | None = None
    game_loop: GameLoop | None = None
    tray: TrayManager | None = None

    try:
        overlay = TransparentOverlay()
        logger.info(
            "Overlay created: {}x{}",
            overlay.width,
            overlay.height,
        )

        # 初始化游戏世界
        world = World(config, overlay)
        world.initialize()
        logger.info("World initialized: {} factions, {} units",
                     len(world.factions), len(world.units))

        # 创建主循环
        game_loop = GameLoop(config, overlay)
        game_loop.world = world
        game_loop.physics_engine = world.physics

        # 启动系统托盘 (独立线程)
        tray = TrayManager(game_loop)
        tray.start()
        logger.info("System tray started")

        # 启动覆盖层渲染线程
        overlay.start()
        logger.info("Overlay render thread started")

        # 启动主循环 (阻塞)
        game_loop.start()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
    finally:
        # 清理
        if tray is not None:
            tray.stop()
        if overlay is not None:
            overlay.stop()
        if game_loop is not None:
            game_loop.stop()
        logger.info("Desktop Battle - Shutdown complete")


if __name__ == "__main__":
    main()
