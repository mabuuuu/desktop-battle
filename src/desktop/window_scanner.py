"""Desktop Battle - 桌面窗口扫描.

枚举桌面窗口，将其边框转换为可攀爬/可站立的平台物理体。
"""

from __future__ import annotations

from dataclasses import dataclass

import win32api
import win32con
import win32gui


@dataclass
class PlatformData:
    """窗口平台数据."""

    rect: tuple[int, int, int, int]  # (left, top, right, bottom)
    title: str
    hwnd: int

    @property
    def left(self) -> int:
        return self.rect[0]

    @property
    def top(self) -> int:
        return self.rect[1]

    @property
    def right(self) -> int:
        return self.rect[2]

    @property
    def bottom(self) -> int:
        return self.rect[3]

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def scan_desktop_windows() -> list[PlatformData]:
    """枚举桌面可见窗口，生成平台数据列表.

    过滤条件:
    - 窗口可见 (IsWindowVisible)
    - 非最小化 (not IsIconic)
    - 有一定的尺寸 (width > 100 and height > 100)
    - 非任务栏窗口
    - 非透明覆盖层窗口

    Returns:
        平台数据列表
    """
    platforms: list[PlatformData] = []

    def enum_callback(hwnd: int, _param: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True

        # 跳过最小化窗口
        if win32gui.IsIconic(hwnd):
            return True

        # 获取窗口矩形
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception:
            return True

        w = rect[2] - rect[0]
        h = rect[3] - rect[1]

        # 过滤太小的窗口
        if w < 100 or h < 100:
            return True

        # 过滤全屏窗口（可能是覆盖层本身）
        screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        if w >= screen_w and h >= screen_h:
            return True

        # 过滤任务栏
        class_name = win32gui.GetClassName(hwnd)
        if "Tray" in class_name or "Shell" in class_name:
            return True

        # 获取标题
        try:
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            title = ""

        # 跳过无标题/系统窗口
        if not title.strip():
            return True

        platforms.append(PlatformData(rect=rect, title=title, hwnd=hwnd))
        return True

    win32gui.EnumWindows(enum_callback, None)
    return platforms


def platforms_to_terrain_segments(
    platforms: list[PlatformData],
    screen_height: int,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """将平台数据转换为 pymunk 地形线段列表.

    每个窗口生成:
    - 顶部: 可站立平台线段
    - 左侧: 可攀爬墙壁线段
    - 右侧: 可攀爬墙壁线段

    Returns:
        [(p1, p2), ...] (pymunk 坐标系)
    """
    from src.desktop.coord import screen_to_physics  # noqa: PLC0415

    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for platform in platforms:
        left, top, right, bottom = platform.rect

        # 顶部平台线段
        p1 = screen_to_physics(float(left), float(top), screen_height)
        p2 = screen_to_physics(float(right), float(top), screen_height)
        segments.append((p1, p2))

        # 左侧攀爬墙壁
        p1 = screen_to_physics(float(left), float(top), screen_height)
        p2 = screen_to_physics(float(left), float(bottom), screen_height)
        segments.append((p1, p2))

        # 右侧攀爬墙壁
        p1 = screen_to_physics(float(right), float(top), screen_height)
        p2 = screen_to_physics(float(right), float(bottom), screen_height)
        segments.append((p1, p2))

    return segments
