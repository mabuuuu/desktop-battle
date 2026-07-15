"""Desktop Battle - 系统托盘图标 + 右键菜单.

使用 infi.systray 创建 Windows 系统托盘图标 (基于 Shell_NotifyIcon API)。
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from infi.systray import SysTrayIcon

if TYPE_CHECKING:
    from src.core.game_loop import GameLoop


class TrayManager:
    """系统托盘管理器.

    提供托盘图标和右键菜单：
    - 继续/暂停
    - 面板
    - 设置
    - 退出
    """

    def __init__(self, game_loop: GameLoop) -> None:
        self._game_loop: GameLoop = game_loop

        # 菜单格式: (文本, 图标路径或None, 回调函数或SysTrayIcon.QUIT)
        self._menu: tuple = (
            ("Pause/Resume", None, self._on_toggle_pause),
            ("Panel", None, self._on_toggle_panel),
            ("Settings", None, self._on_open_settings),
        )

        self._systray: SysTrayIcon | None = None
        self._panel_visible: bool = False

    def start(self) -> None:
        """在独立线程中启动系统托盘."""

        def _run() -> None:
            try:
                self._systray = SysTrayIcon(
                    "",  # 空字符串 = 使用默认图标
                    "Desktop Battle - 桌面火柴人大乱斗",
                    self._menu,
                    on_quit=self._on_quit,
                )
                self._systray.start()
            except Exception:
                pass  # 后台静默失败，不影响主游戏

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def stop(self) -> None:
        """停止系统托盘."""
        if self._systray is not None:
            try:
                self._systray.shutdown()
            except Exception:
                pass

    def _on_toggle_pause(self, systray: SysTrayIcon) -> None:
        """切换暂停状态."""
        self._game_loop.toggle_pause()

    def _on_toggle_panel(self, systray: SysTrayIcon) -> None:
        """切换信息面板."""
        self._panel_visible = not self._panel_visible

    def _on_open_settings(self, systray: SysTrayIcon) -> None:
        """打开设置对话框 (Phase 11)."""
        pass

    def _on_quit(self, systray: SysTrayIcon) -> None:
        """退出程序."""
        self._game_loop.stop()
