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
    DEFAULT_WIDTH: int = 280
    HEADER_HEIGHT: int = 24
    ROW_HEIGHT: int = 16
    PADDING: int = 6

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
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0
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
        """处理鼠标按下事件，用于拖拽.

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

        # 拖拽标题栏
        if self._x <= mx <= self._x + self._width and self._y <= my <= self._y + self.HEADER_HEIGHT:
            self._dragging = True
            self._drag_offset_x = mx - self._x
            self._drag_offset_y = my - self._y
            return True

        return False

    def handle_mouse_move(self, mx: int, my: int) -> None:
        """处理鼠标移动（拖拽）."""
        if self._dragging:
            self._x = mx - self._drag_offset_x
            self._y = my - self._drag_offset_y

    def handle_mouse_up(self) -> None:
        """结束拖拽."""
        self._dragging = False

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
        """渲染面板到 RGBA 缓冲.

        Args:
            buffer: numpy (H, W, 4) RGBA 缓冲
        """
        if not self._visible:
            return

        from src.render.sprite import draw_rect, draw_line, draw_text

        panel_h = self._calculate_height()
        x, y, w = self._x, self._y, self._width

        # 半透明背景
        bg_color = (20, 20, 40, 210)
        draw_rect(buffer, float(x), float(y), w, panel_h, bg_color, 0)

        # 标题栏
        header_bg = (40, 40, 70, 230)
        draw_rect(buffer, float(x), float(y), w, self.HEADER_HEIGHT, header_bg, 0)

        # 标题文字
        draw_text(buffer, float(x + 6), float(y + 4), "Desktop Battle", (200, 200, 255, 255), 10)

        # 关闭按钮
        cx = x + w - 16
        cy = y + 4
        draw_text(buffer, float(cx), float(cy), "X", (255, 100, 100, 255), 10)

        # 分隔线
        line_y = y + self.HEADER_HEIGHT
        draw_line(buffer, float(x), float(line_y), float(x + w), float(line_y), (80, 80, 120, 150), 1)

        # 运行时间
        mins = int(self._world.elapsed_time // 60)
        secs = int(self._world.elapsed_time % 60)
        draw_text(buffer, float(x + 6), float(line_y + 4), f"Time: {mins:02d}:{secs:02d}", (180, 180, 200, 200), 9)

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
        """渲染单个阵营的信息行.

        Returns:
            下一行的 Y 坐标
        """
        from src.render.sprite import draw_rect, draw_text

        x = panel_x
        y = start_y
        color = stats["color"]
        r, g, b = self._hex_to_rgb(str(color))

        # 阵营名 + 颜色条
        draw_rect(buffer, float(x + 4), float(y - 1), 10, 10, (r, g, b, 200), 0)
        name = str(stats["name"])
        strategy = str(stats["strategy"])
        draw_text(buffer, float(x + 18), float(y), f"{name} [{strategy}]", (r, g, b, 240), 10)
        y += 14

        # 资源
        wood = int(stats["wood"])
        ore = int(stats["ore"])
        draw_text(buffer, float(x + 10), float(y), f"W:{wood} O:{ore}", (180, 200, 180, 220), 9)
        y += 12

        # 单位
        alive = int(stats["alive"])
        dead = int(stats["dead"])
        total = int(stats["total"])
        produced = int(stats["units_produced"])
        lost = int(stats["units_lost"])
        draw_text(
            buffer, float(x + 10), float(y),
            f"Units: {alive} (+{produced}) / {lost} lost (dead:{dead})",
            (180, 180, 220, 220), 9,
        )
        y += 12

        # 建筑 + 武器
        wb = int(stats["workbenches"])
        max_bench = int(stats["max_bench"])
        br = int(stats["barracks"])
        weapons = int(stats["weapon_count"])
        draw_text(
            buffer, float(x + 10), float(y),
            f"Build: WB={wb}(Lv{max_bench}) Bx={br} | Armed: {weapons}",
            (180, 180, 220, 220), 9,
        )
        y += 14

        return y

    def _calculate_height(self) -> int:
        """计算面板高度."""
        rows_per_faction = 4
        faction_lines = rows_per_faction * 14 * len(self._world.factions) if self._world.factions else 0
        return self.HEADER_HEIGHT + 24 + faction_lines + 8

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
