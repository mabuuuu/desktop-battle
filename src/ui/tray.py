"""Desktop Battle - 系统托盘图标 + 右键菜单.

使用 infi.systray 创建 Windows 系统托盘图标 (基于 Shell_NotifyIcon API)。
联动信息面板和设置管理器。
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from infi.systray import SysTrayIcon

if TYPE_CHECKING:
    from src.core.game_loop import GameLoop
    from src.ui.panel import InfoPanel
    from src.ui.settings_dialog import SettingsDialog


class TrayManager:
    """系统托盘管理器.

    提供托盘图标和右键菜单：
    - 继续/暂停
    - 面板 (开关)
    - 设置
    - 退出
    """

    def __init__(self, game_loop: GameLoop, panel: InfoPanel | None = None) -> None:
        self._game_loop: GameLoop = game_loop
        self._panel: InfoPanel | None = panel
        self._settings_dialog: SettingsDialog | None = None

        # 菜单格式: (文本, 图标路径或None, 回调函数或SysTrayIcon.QUIT)
        self._menu: tuple = (
            ("暂停 / 继续", None, self._on_toggle_pause),
            ("信息面板", None, self._on_toggle_panel),
            ("设置", None, self._on_open_settings),
        )

        self._systray: SysTrayIcon | None = None

    def set_panel(self, panel: InfoPanel) -> None:
        """设置关联的面板引用."""
        self._panel = panel

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
        """切换信息面板显示."""
        if self._panel is not None:
            self._panel.toggle()

    def _on_open_settings(self, systray: SysTrayIcon) -> None:
        """打开设置弹窗."""
        from src.ui.settings_dialog import SettingsDialog
        try:
            if self._settings_dialog is None or not self._settings_dialog.is_open:
                self._settings_dialog = SettingsDialog(self._game_loop)
                self._settings_dialog.show()
        except Exception:
            pass

    def _on_quit(self, systray: SysTrayIcon) -> None:
        """退出程序."""
        # 保存设置
        try:
            from src.ui.settings import SettingsManager
            SettingsManager.get_instance().save()
        except Exception:
            pass
        self._game_loop.stop()
