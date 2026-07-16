"""Desktop Battle - 信息面板.

在游戏覆盖层上渲染半透明信息面板，显示双方阵营参数。
通过 numpy RGBA 缓冲直接绘制，不创建额外窗口。
支持拖拽移动、关闭按钮，每0.5秒刷新数据。
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.core.world import World
    from src.entity.faction import Faction


class InfoPanel:
    """游戏信息面板.

    显示内容:
    - 阵营名称和颜色标识
    - 资源: 木材/矿石
    - 单位: 存活数/阵亡数/总数
    - 建筑: 工具台/兵营数量
    - 武器: 制作中/已装备统计
    - 当前策略
    - 运行时间
    """

    # 面板尺寸
    DEFAULT_WIDTH: int = 300
    HEADER_HEIGHT: int = 24
    ROW_HEIGHT: int = 16
    PADDING: int = 6
    MIN_WIDTH: int = 200
    MAX_WIDTH: int = 600

    def __init__(
        self,
        world: World,
        x: int = 10,
        y: int = 50,
        width: int | None = None,
    ) -> None:
        self._world: World = world
        self._x: int = x
        self._y: int = y
        self._width: int = width or self.DEFAULT_WIDTH
        self._visible: bool = True
        self._dragging: bool = False
        self._resizing: bool = False
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0
        self._resize_start_x: int = 0
        self._resize_start_width: int = 0
        self._last_refresh: float = 0.0
        self._refresh_interval: float = 0.5  # 0.5秒刷新

        # 缓存
        self._faction_stats: list[dict[str, object]] = []

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    def toggle(self) -> bool:
        """切换显示/隐藏."""
        self._visible = not self._visible
        return self._visible

    def handle_mouse_down(self, mx: int, my: int) -> bool:
        """处理鼠标按下事件，用于拖拽和缩放.

        Returns:
            是否消费了事件
        """
        if not self._visible:
            return False

        h = self._calculate_height()
        # 点击关闭按钮
        close_btn_x = self._x + self._width - 16
        close_btn_y = self._y + 2
        if close_btn_x <= mx <= close_btn_x + 12 and close_btn_y <= my <= close_btn_y + 12:
            self._visible = False
            return True

        # 右边缘缩放 (8px热区)
        resize_zone_x = self._x + self._width - 8
        if abs(mx - (self._x + self._width)) < 8 and self._y <= my <= self._y + h:
            self._resizing = True
            self._resize_start_x = mx
            self._resize_start_width = self._width
            return True

        # 拖拽标题栏
        if self._x <= mx <= self._x + self._width and self._y <= my <= self._y + self.HEADER_HEIGHT:
            self._dragging = True
            self._drag_offset_x = mx - self._x
            self._drag_offset_y = my - self._y
            return True

        return False

    def handle_mouse_move(self, mx: int, my: int) -> None:
        """处理鼠标移动（拖拽/缩放）."""
        if self._dragging:
            self._x = mx - self._drag_offset_x
            self._y = my - self._drag_offset_y
        elif self._resizing:
            dx = mx - self._resize_start_x
            new_width = self._resize_start_width + dx
            self._width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, new_width))

    def handle_mouse_up(self) -> None:
        """结束拖拽/缩放."""
        self._dragging = False
        self._resizing = False

    def update(self, now: float) -> None:
        """定期刷新数据."""
        if now - self._last_refresh >= self._refresh_interval:
            self._refresh_stats()
            self._last_refresh = now

    def _refresh_stats(self) -> None:
        """刷新阵营统计数据."""
        self._faction_stats = []
        for faction in self._world.factions:
            workbenches = faction.get_buildings_by_type("workbench")
            barracks = faction.get_buildings_by_type("barracks")
            bench_levels = [b.level for b in workbenches]
            max_bench = max(bench_levels) if bench_levels else 0

            # 统计武器
            units_with_weapon = sum(
                1 for u in faction.alive_units if u.weapon is not None
            )

            self._faction_stats.append({
                "name": faction.name,
                "color": faction.color_hex,
                "wood": faction.wood,
                "ore": faction.ore,
                "alive": faction.alive_count,
                "dead": faction.dead_units,
                "total": len(faction.units),
                "workbenches": len(workbenches),
                "max_bench": max_bench,
                "barracks": len(barracks),
                "weapon_count": units_with_weapon,
                "strategy": faction.current_strategy,
                "units_produced": faction.units_produced,
                "units_lost": faction.units_lost,
                "buildings_built": faction.buildings_built,
            })

    def render(self, buffer: np.ndarray) -> None:
        """渲染面板（使用 overlay 原生 API 支持中文）.

        Args:
            buffer: numpy (H, W, 4) RGBA 缓冲（用于背景绘制）
        """
        if not self._visible:
            return

        from src.render.sprite import draw_rect, draw_line, draw_text

        panel_h = self._calculate_height()
        x, y, w = self._x, self._y, self._width

        # 半透明背景
        bg_color = (20, 20, 40, 180)
        draw_rect(buffer, float(x), float(y), w, panel_h, bg_color, 0)

        # 标题栏
        header_bg = (40, 40, 70, 230)
        draw_rect(buffer, float(x), float(y), w, self.HEADER_HEIGHT, header_bg, 0)

        # 标题 — 使用 overlay 原生文本支持中文
        overlay = getattr(self._world, 'overlay', None)
        if overlay is not None:
            overlay.draw_text(x + 6, y + 2, "Desktop Battle", (200, 200, 255, 255), 14.0)
            # 关闭按钮
            overlay.draw_text(x + w - 18, y + 2, "×", (255, 100, 100, 255), 14.0)

        # 分隔线
        line_y = y + self.HEADER_HEIGHT
        draw_line(buffer, float(x), float(line_y), float(x + w), float(line_y), (80, 80, 120, 150), 1)

        # 运行时间
        mins = int(self._world.elapsed_time // 60)
        secs = int(self._world.elapsed_time % 60)
        if overlay is not None:
            overlay.draw_text(x + 6, line_y + 2, f"运行时间: {mins:02d}:{secs:02d}", (180, 180, 200, 200), 12.0)

        # 缩放提示（右边缘）
        draw_line(buffer, float(x + w - 3), float(y), float(x + w - 3), float(y + panel_h), (100, 100, 180, 100), 2)

        # 阵营信息
        row_y = float(line_y + 22)
        for stats in self._faction_stats:
            row_y = self._render_faction_row(buffer, x, row_y, w, stats)

        # 底部边框
        draw_rect(buffer, float(x), float(y), w, panel_h, (60, 60, 90, 200), 1)

    def _render_faction_row(
        self,
        buffer: np.ndarray,
        panel_x: int,
        start_y: float,
        panel_w: int,
        stats: dict[str, object],
    ) -> float:
        """渲染单个阵营的信息行（中文）.

        Returns:
            下一行的 Y 坐标
        """
        from src.render.sprite import draw_rect

        x = panel_x
        y = start_y
        color = stats["color"]
        r, g, b = self._hex_to_rgb(str(color))

        overlay = getattr(self._world, 'overlay', None)

        # 阵营名 + 颜色条
        draw_rect(buffer, float(x + 4), float(y - 1), 10, 10, (r, g, b, 200), 0)
        name = str(stats["name"])
        strategy = str(stats["strategy"])
        strategy_cn = {
            "expand": "扩张",
            "rush": "突击",
            "defense": "防御",
            "tech": "科技",
        }.get(strategy, strategy)
        if overlay is not None:
            overlay.draw_text(x + 18, int(y) - 2, f"{name} [{strategy_cn}]", (r, g, b, 240), 12.0)
        y += 16

        # 资源
        wood = int(stats["wood"])
        ore = int(stats["ore"])
        if overlay is not None:
            overlay.draw_text(x + 10, int(y) - 2, f"木材:{wood}  矿石:{ore}", (180, 200, 180, 220), 11.0)
        y += 14

        # 单位
        alive = int(stats["alive"])
        dead = int(stats["dead"])
        produced = int(stats["units_produced"])
        lost = int(stats["units_lost"])
        if overlay is not None:
            overlay.draw_text(
                x + 10, int(y) - 2,
                f"存活:{alive}(+{produced})  阵亡:{lost}",
                (180, 180, 220, 220), 11.0,
            )
        y += 14

        # 建筑 + 武器
        wb = int(stats["workbenches"])
        max_bench = int(stats["max_bench"])
        br = int(stats["barracks"])
        weapons = int(stats["weapon_count"])
        if overlay is not None:
            overlay.draw_text(
                x + 10, int(y) - 2,
                f"工具台:{wb}(Lv{max_bench}) 兵营:{br} 武装:{weapons}",
                (180, 180, 220, 220), 11.0,
            )
        y += 16

        return y

    def render_overlay(self, overlay: object) -> None:
        """使用overlay直接API渲染面板（高性能，纯overlay版本）."""
        if not self._visible:
            return

        panel_h = self._calculate_height()
        x, y, w = self._x, self._y, self._width

        # 半透明背景
        overlay.draw_rect(x, y, w, panel_h, (20, 20, 40, 180), 0)

        # 标题栏
        overlay.draw_rect(x, y, w, self.HEADER_HEIGHT, (40, 40, 70, 230), 0)

        # 标题文本
        overlay.draw_text(x + 6, y + 2, "Desktop Battle", (200, 200, 255, 255), 14.0)
        overlay.draw_text(x + w - 18, y + 2, "×", (255, 100, 100, 255), 14.0)

        # 分隔线
        line_y = y + self.HEADER_HEIGHT
        overlay.draw_line(x, line_y, x + w, line_y, (80, 80, 120, 150), 1)

        # 运行时间
        mins = int(self._world.elapsed_time // 60)
        secs = int(self._world.elapsed_time % 60)
        overlay.draw_text(x + 6, line_y + 2, f"运行时间: {mins:02d}:{secs:02d}", (180, 180, 200, 200), 12.0)

        # 缩放提示
        overlay.draw_line(x + w - 3, y, x + w - 3, y + panel_h, (100, 100, 180, 100), 2)

        # 阵营信息
        row_y = float(line_y + 22)
        for stats in self._faction_stats:
            row_y = self._render_faction_row_overlay(overlay, x, row_y, w, stats)

        # 底部边框
        overlay.draw_rect(x, y, w, panel_h, (60, 60, 90, 200), 1)

    def _render_faction_row_overlay(
        self,
        overlay: object,
        panel_x: int,
        start_y: float,
        panel_w: int,
        stats: dict[str, object],
    ) -> float:
        """使用overlay直接API渲染单个阵营信息行."""
        x = panel_x
        y = start_y
        color = stats["color"]
        r, g, b = self._hex_to_rgb(str(color))

        # 阵营名 + 颜色条
        overlay.draw_rect(x + 4, int(y) - 1, 10, 10, (r, g, b, 200), 0)
        name = str(stats["name"])
        strategy = str(stats["strategy"])
        strategy_cn = {
            "expand": "扩张",
            "rush": "突击",
            "defense": "防御",
            "tech": "科技",
        }.get(strategy, strategy)
        overlay.draw_text(x + 18, int(y) - 2, f"{name} [{strategy_cn}]", (r, g, b, 240), 12.0)
        y += 16

        # 资源
        wood = int(stats["wood"])
        ore = int(stats["ore"])
        overlay.draw_text(x + 10, int(y) - 2, f"木材:{wood}  矿石:{ore}", (180, 200, 180, 220), 11.0)
        y += 14

        # 单位
        alive = int(stats["alive"])
        produced = int(stats["units_produced"])
        lost = int(stats["units_lost"])
        overlay.draw_text(
            x + 10, int(y) - 2,
            f"存活:{alive}(+{produced})  阵亡:{lost}",
            (180, 180, 220, 220), 11.0,
        )
        y += 14

        # 建筑 + 武器
        wb = int(stats["workbenches"])
        max_bench = int(stats["max_bench"])
        br = int(stats["barracks"])
        weapons = int(stats["weapon_count"])
        overlay.draw_text(
            x + 10, int(y) - 2,
            f"工具台:{wb}(Lv{max_bench}) 兵营:{br} 武装:{weapons}",
            (180, 180, 220, 220), 11.0,
        )
        y += 16

        return y

    def _calculate_height(self) -> int:
        """计算面板高度."""
        rows_per_faction = 4
        faction_lines = rows_per_faction * 16 * len(self._world.factions) if self._world.factions else 0
        return self.HEADER_HEIGHT + 28 + faction_lines + 8

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """HEX → RGB."""
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def is_point_inside(self, px: int, py: int) -> bool:
        """检查点是否在面板内."""
        if not self._visible:
            return False
        h = self._calculate_height()
        return self._x <= px <= self._x + self._width and self._y <= py <= self._y + h
