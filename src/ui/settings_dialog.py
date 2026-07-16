"""Desktop Battle - 设置弹窗.

使用 tkinter 创建设置窗口，支持调整游戏参数:
- 游戏速度
- 移动速度倍率
- 单位缩放
- 重力
- 伤害倍率
- 初始单位数
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.game_loop import GameLoop


class SettingsDialog:
    """设置弹窗.

    点击托盘"设置"菜单项时弹出，暂停游戏并显示参数调节界面。
    关闭窗口时自动保存设置并恢复游戏。
    """

    def __init__(self, game_loop: GameLoop) -> None:
        self._game_loop = game_loop
        self._window: tk.Tk | None = None
        self._open: bool = False

    @property
    def is_open(self) -> bool:
        return self._open

    def show(self) -> None:
        """显示设置弹窗（线程安全）."""
        if self._open:
            return
        self._open = True
        # tkinter 必须在主线程运行，但游戏循环在主线程
        # 所以在独立线程中运行 tkinter
        t = threading.Thread(target=self._run_dialog, daemon=True)
        t.start()

    def _run_dialog(self) -> None:
        """在独立线程中运行 tkinter 对话框."""
        try:
            self._window = tk.Tk()
            self._window.title("桌面大乱斗 - 设置")
            self._window.geometry("420x520")
            self._window.resizable(True, True)
            self._window.configure(bg="#1a1a2e")

            # 暂停游戏
            self._game_loop.paused = True

            self._build_ui()
            self._window.protocol("WM_DELETE_WINDOW", self._on_close)
            self._window.mainloop()
        except Exception:
            pass
        finally:
            self._open = False
            self._window = None
            # 恢复游戏
            self._game_loop.paused = False

    def _build_ui(self) -> None:
        """构建设置界面."""
        w = self._window
        if w is None:
            return

        from src.ui.settings import SettingsManager
        sm = SettingsManager.get_instance()
        s = sm.settings

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", background="#1a1a2e", foreground="#e0e0ff", font=("Microsoft YaHei", 14, "bold"))
        style.configure("Section.TLabel", background="#1a1a2e", foreground="#a0a0d0", font=("Microsoft YaHei", 10, "bold"))
        style.configure("Setting.TLabel", background="#1a1a2e", foreground="#c0c0e0", font=("Microsoft YaHei", 9))
        style.configure("Value.TLabel", background="#1a1a2e", foreground="#80ff80", font=("Microsoft YaHei", 9))
        style.configure("TScale", background="#1a1a2e", troughcolor="#2a2a4e")

        # 标题
        ttk.Label(w, text="⚙ 游戏设置", style="Title.TLabel").pack(pady=(15, 10))

        # ── 游戏速度 ──
        self._add_section(w, "游戏速度")
        self._game_speed_var = tk.DoubleVar(value=s.game_speed)
        self._game_speed_label = self._add_slider(
            w, "游戏速度倍率", self._game_speed_var, 0.1, 3.0, 0.1,
            f"{s.game_speed:.1f}x",
        )

        # ── 移动 ──
        self._add_section(w, "移动")
        self._move_speed_var = tk.DoubleVar(value=s.move_speed_multiplier)
        self._move_speed_label = self._add_slider(
            w, "移动速度倍率", self._move_speed_var, 0.5, 3.0, 0.1,
            f"{s.move_speed_multiplier:.1f}x",
        )

        # ── 缩放 ──
        self._add_section(w, "单位缩放")
        self._unit_scale_var = tk.DoubleVar(value=getattr(s, 'unit_scale', 1.0))
        self._unit_scale_label = self._add_slider(
            w, "单位整体缩放", self._unit_scale_var, 0.5, 3.0, 0.1,
            f"{getattr(s, 'unit_scale', 1.0):.1f}x",
        )

        # ── 物理 ──
        self._add_section(w, "物理")
        self._gravity_var = tk.DoubleVar(value=s.gravity)
        self._gravity_label = self._add_slider(
            w, "重力加速度", self._gravity_var, 100.0, 2000.0, 50.0,
            f"{s.gravity:.0f}",
        )

        # ── 战斗 ──
        self._add_section(w, "战斗")
        self._damage_var = tk.DoubleVar(value=s.damage_multiplier)
        self._damage_label = self._add_slider(
            w, "伤害倍率", self._damage_var, 0.5, 5.0, 0.1,
            f"{s.damage_multiplier:.1f}x",
        )

        # ── 初始设置 ──
        self._add_section(w, "初始设置")
        self._initial_units_var = tk.IntVar(value=s.initial_units)
        self._initial_units_label = self._add_slider(
            w, "初始单位数", self._initial_units_var, 1, 15, 1,
            f"{s.initial_units}",
        )

        # ── 按钮 ──
        btn_frame = tk.Frame(w, bg="#1a1a2e")
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="保存并关闭", command=self._on_save,
            bg="#2a4a2a", fg="#80ff80", font=("Microsoft YaHei", 10, "bold"),
            padx=20, pady=5,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="取消", command=self._on_close,
            bg="#4a2a2a", fg="#ff8080", font=("Microsoft YaHei", 10),
            padx=20, pady=5,
        ).pack(side=tk.LEFT, padx=10)

    def _add_section(self, parent: tk.Tk, title: str) -> None:
        """添加分节标题."""
        frame = tk.Frame(parent, bg="#1a1a2e")
        frame.pack(fill=tk.X, padx=20, pady=(10, 2))
        ttk.Label(frame, text=f"── {title} ──", style="Section.TLabel").pack(anchor=tk.W)

    def _add_slider(
        self,
        parent: tk.Tk,
        label: str,
        var: tk.Variable,
        from_: float,
        to: float,
        resolution: float,
        initial_text: str,
    ) -> ttk.Label:
        """添加一个滑块设置项.

        Returns:
            值标签，用于实时更新
        """
        frame = tk.Frame(parent, bg="#1a1a2e")
        frame.pack(fill=tk.X, padx=25, pady=2)

        ttk.Label(frame, text=label, style="Setting.TLabel").pack(side=tk.LEFT)

        value_label = ttk.Label(frame, text=initial_text, style="Value.TLabel")
        value_label.pack(side=tk.RIGHT)

        slider = ttk.Scale(
            frame,
            from_=from_,
            to=to,
            variable=var,
            orient=tk.HORIZONTAL,
            command=lambda v, vl=value_label, vr=var, res=resolution: self._on_slider_change(vl, vr, res),
        )
        slider.pack(fill=tk.X, padx=(10, 10))

        return value_label

    def _on_slider_change(self, label: ttk.Label, var: tk.Variable, resolution: float) -> None:
        """滑块值变化回调."""
        val = var.get()
        # 对齐到分辨率
        if resolution >= 1:
            val = round(val / resolution) * resolution
            label.config(text=f"{int(val)}")
        else:
            val = round(val / resolution) * resolution
            label.config(text=f"{val:.1f}x" if val < 100 else f"{val:.0f}")

    def _on_save(self) -> None:
        """保存设置."""
        from src.ui.settings import SettingsManager
        sm = SettingsManager.get_instance()

        sm.settings.game_speed = self._game_speed_var.get()
        sm.settings.move_speed_multiplier = self._move_speed_var.get()
        sm.settings.gravity = self._gravity_var.get()
        sm.settings.damage_multiplier = self._damage_var.get()
        sm.settings.initial_units = int(self._initial_units_var.get())

        # 单位缩放
        unit_scale = self._unit_scale_var.get()
        sm.settings.unit_scale = unit_scale  # type: ignore[attr-defined]

        # 应用到 GameConfig
        if self._game_loop.world is not None:
            config = self._game_loop.world.config  # type: ignore[union-attr]
            sm.apply_to_config(config)
            # 应用缩放到渲染参数
            config.stickman_height = int(20 * unit_scale)
            config.stickman_line_width = max(1, int(1 * unit_scale))
            config.stickman_head_radius = max(1, int(2 * unit_scale))

        sm.save()
        self._on_close()

    def _on_close(self) -> None:
        """关闭窗口."""
        if self._window is not None:
            self._window.destroy()
        self._open = False
        self._game_loop.paused = False
