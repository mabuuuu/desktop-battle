"""Desktop Battle - 透明窗口覆盖层封装.

封装 transparent_overlay.Overlay，配置窗口穿透/置顶/工具窗口。
"""

from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING

import numpy as np
import win32api
import win32con
import win32gui
from transparent_overlay import Overlay as _Overlay

if TYPE_CHECKING:
    pass


class TransparentOverlay:
    """透明覆盖层窗口管理器.

    封装 transparent_overlay 库，提供 WS_EX_TRANSPARENT
    实现点击穿透，WS_EX_TOPMOST 置顶，WS_EX_TOOLWINDOW 隐藏任务栏图标。
    """

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """初始化覆盖层.

        Args:
            x: 窗口X坐标 (默认0，全屏)
            y: 窗口Y坐标 (默认0，全屏)
            width: 窗口宽度 (默认屏幕宽度)
            height: 窗口高度 (默认屏幕高度)
        """
        self._started: bool = False
        self._overlay = _Overlay(x=x, y=y, width=width, height=height)
        self._width: int = width or win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self._height: int = height or win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        self._hwnd: int = 0

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def hwnd(self) -> int:
        """获取覆盖层窗口句柄."""
        if self._hwnd:
            return self._hwnd
        # 查找覆盖层窗口
        self._hwnd = _find_overlay_hwnd()
        return self._hwnd

    def start(self) -> None:
        """启动覆盖层渲染线程并设置窗口样式."""
        if self._started:
            return
        self._overlay.start_layer()
        self._started = True
        # 追加 WS_EX_TRANSPARENT 实现点击穿透
        hwnd = self.hwnd
        if hwnd:
            _add_window_style(hwnd, win32con.WS_EX_TRANSPARENT)

    def stop(self) -> None:
        """停止覆盖层."""
        if not self._started:
            return
        self._overlay.stop_layer()
        self._started = False

    def clear_frame(self) -> None:
        """清空当前帧缓冲."""
        self._overlay.frame_clear()

    def signal_render(self) -> None:
        """提交当前帧到显示."""
        self._overlay.signal_render()

    def render_numpy_buffer(self, buffer: np.ndarray, sprite_key: str = "frame") -> None:
        """将 numpy RGBA 数组渲染到覆盖层.

        Args:
            buffer: (height, width, 4) uint8 RGBA 数组
            sprite_key: 精灵缓存键
        """
        self.clear_frame()
        self._overlay.create_sprite_from_numpy(buffer, sprite_key)
        self._overlay.add_sprite_instance(sprite_key, 0, 0)
        self.signal_render()

    def draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 1,
    ) -> None:
        """直接在覆盖层上画线（不经过 numpy 缓冲）."""
        self._overlay.draw_line(x1, y1, x2, y2, color, thickness)

    def draw_circle(
        self,
        x: int,
        y: int,
        radius: int,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 0,
    ) -> None:
        """直接在覆盖层上画圆."""
        self._overlay.draw_circle(x, y, radius, color, thickness)

    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        thickness: int = 0,
    ) -> None:
        """直接在覆盖层上画矩形."""
        self._overlay.draw_rect(x, y, width, height, color, thickness)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        font_size: float = 16.0,
    ) -> None:
        """直接在覆盖层上绘制文本."""
        self._overlay.draw_text(x, y, text, color, font_size)

    def __enter__(self) -> TransparentOverlay:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.stop()
        return False

    def __del__(self) -> None:
        if self._started:
            self.stop()


def _find_overlay_hwnd() -> int:
    """查找 transparent_overlay 创建的窗口句柄."""
    # transparent_overlay 使用特定类名，遍历顶层窗口查找
    result: list[int] = []

    def enum_callback(hwnd: int, _param: object) -> bool:
        class_name = win32gui.GetClassName(hwnd)
        # transparent_overlay 创建的窗口类名通常包含 "Overlay"
        if "Overlay" in class_name or "Transparent" in class_name:
            result.append(hwnd)
            return False  # 找到后停止
        return True

    win32gui.EnumWindows(enum_callback, None)
    return result[0] if result else 0


def _add_window_style(hwnd: int, style: int) -> None:
    """向窗口追加扩展样式."""
    current = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, current | style)
    # 刷新窗口以应用新样式
    ctypes.windll.user32.SetWindowPos(
        hwnd,
        0,
        0,
        0,
        0,
        0,
        0x0002 | 0x0001 | 0x0020,  # SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED
    )
