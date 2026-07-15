"""Desktop Battle - 主循环框架.

帧率控制、暂停支持、物理/行为/渲染更新调度。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from src.core.config import GameConfig
    from src.render.overlay import TransparentOverlay


class GameLoop:
    """主游戏循环.

    每帧执行:
    1. 物理更新 (pymunk space.step)
    2. 行为更新 (每 N 帧 tick 行为树)
    3. 渲染更新 (绘制所有实体到 RGBA 缓冲并提交)
    """

    def __init__(self, config: GameConfig, overlay: TransparentOverlay) -> None:
        self.config: GameConfig = config
        self.overlay: TransparentOverlay = overlay
        self.paused: bool = False
        self.running: bool = False
        self.frame_count: int = 0
        self.physics_engine: object | None = None
        self.world: object | None = None

        # 帧率统计
        self._last_fps_report_time: float = 0.0
        self._fps_frame_count: int = 0
        self._current_fps: float = 0.0

        # 渲染缓冲
        self._render_buffer: np.ndarray | None = None

    def start(self) -> None:
        """启动主循环."""
        logger.info(
            "Engine started | FPS target: {} | Screen: {}x{}",
            self.config.target_fps,
            self.overlay.width,
            self.overlay.height,
        )
        self.running = True
        self._render_buffer = np.zeros(
            (self.overlay.height, self.overlay.width, 4), dtype=np.uint8
        )
        self._last_fps_report_time = time.time()

        # 日志系统
        try:
            from src.game_logging.system_log import log_game_start
            log_game_start(f"FPS={self.config.target_fps}")
        except Exception:
            pass

        try:
            self._run_loop()
        finally:
            self.running = False
            elapsed = time.time() - self._last_fps_report_time
            logger.info("Engine shutdown | Runtime: {:.1f}s", elapsed)
            try:
                from src.game_logging.system_log import log_game_shutdown
                log_game_shutdown(elapsed)
            except Exception:
                pass

    def stop(self) -> None:
        """停止主循环."""
        self.running = False

    def toggle_pause(self) -> bool:
        """切换暂停状态."""
        self.paused = not self.paused
        if self.paused:
            logger.info("Game paused")
        else:
            logger.info("Game resumed")
        return self.paused

    def _run_loop(self) -> None:
        """内部主循环."""
        target_frame_time = 1.0 / self.config.target_fps

        while self.running:
            frame_start = time.time()

            if not self.paused:
                dt = min(target_frame_time, 1.0 / 30.0)
                effective_dt = dt * self.config.game_speed

                # 1. 物理+世界更新 (包含行为树、攀爬、AI)
                self._update_physics(effective_dt)

                # 2. 渲染
                self._update_render()

                self._fps_frame_count += 1

            # 帧率统计 (每5秒)
            now = time.time()
            elapsed = now - self._last_fps_report_time
            if elapsed >= 5.0 and self._fps_frame_count > 0:
                self._current_fps = self._fps_frame_count / elapsed
                unit_count = self._get_unit_count()
                logger.debug("FPS: {:.0f} | Units: {}", self._current_fps, unit_count)
                try:
                    from src.game_logging.system_log import log_fps
                    log_fps(self._current_fps, unit_count, self.frame_count)
                except Exception:
                    pass
                self._last_fps_report_time = now
                self._fps_frame_count = 0

            # 帧率控制
            frame_end = time.time()
            frame_elapsed = frame_end - frame_start
            if frame_elapsed < target_frame_time:
                time.sleep(target_frame_time - frame_elapsed)

            self.frame_count += 1

    def _update_physics(self, dt: float) -> None:
        """更新游戏世界 (物理+行为+逻辑)."""
        if self.world is not None:
            self.world.update(dt)  # type: ignore[union-attr]

    def _update_behavior(self) -> None:
        """更新行为树 (已合并到 world.update 中)."""
        pass

    def _update_render(self) -> None:
        """渲染所有实体."""
        if self._render_buffer is None:
            return

        if self.world is not None:
            self.world.render(self.overlay, self._render_buffer)  # type: ignore[union-attr]

    def _get_unit_count(self) -> int:
        """获取当前单位总数."""
        if self.world is not None:
            return self.world.get_total_unit_count()  # type: ignore[union-attr]
        return 0
