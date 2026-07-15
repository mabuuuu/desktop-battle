"""Desktop Battle - 任务栏位置检测.

通过 Win32 Shell_TrayWnd 窗口句柄获取任务栏的屏幕矩形。
"""

from dataclasses import dataclass

import win32con
import win32gui

from src.desktop.coord import screen_to_physics


@dataclass(frozen=True)
class Rect:
    """屏幕矩形 (Y轴向下)."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def get_taskbar_rect() -> Rect | None:
    """通过 Win32 API 获取任务栏位置和尺寸.

    任务栏可能在屏幕底部、顶部、左侧或右侧。
    """
    hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
    if hwnd == 0:
        return None
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return Rect(left=left, top=top, right=right, bottom=bottom)


def get_taskbar_ground_physics(
    rect: Rect, screen_height: int
) -> tuple[tuple[float, float], tuple[float, float]]:
    """将任务栏顶部转换为 pymunk 坐标系中的地面线段端点.

    地面 = 任务栏顶部线段。
    返回 ((x1, y1_physics), (x2, y2_physics)).
    """
    p1 = screen_to_physics(float(rect.left), float(rect.top), screen_height)
    p2 = screen_to_physics(float(rect.right), float(rect.top), screen_height)
    return (p1, p2)


def get_taskbar_top_screen_y(rect: Rect) -> int:
    """获取任务栏顶部在屏幕坐标中的 Y 值."""
    return rect.top
