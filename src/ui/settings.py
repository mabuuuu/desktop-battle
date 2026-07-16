"""Desktop Battle - 设置管理器.

持久化游戏设置到 %APPDATA%/DesktopBattle/settings.json。
提供运行时读取/修改设置的能力，支持通过 UI 面板修改。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _get_settings_dir() -> Path:
    """获取设置目录路径."""
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    settings_dir = Path(appdata) / "DesktopBattle"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


def _get_settings_path() -> Path:
    """获取设置文件路径."""
    return _get_settings_dir() / "settings.json"


@dataclass
class RuntimeSettings:
    """运行时游戏设置.

    这些值可以通过设置面板修改，并持久化到磁盘。
    """

    # ── 游戏速度 ──
    game_speed: float = 1.0  # 0.5 ~ 3.0

    # ── 伤害 ──
    damage_multiplier: float = 1.0  # 0.5 ~ 3.0

    # ── 初始单位 ──
    initial_units: int = 5  # 1 ~ 10

    # ── 显示 ──
    show_health_bars: bool = True
    show_info_panel: bool = True

    # ── AI ──
    ai_enabled: bool = False
    ai_api_url: str = "https://api.openai.com/v1/chat/completions"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_interval: float = 15.0

    # ── 物理 ──
    gravity: float = 900.0
    move_speed_multiplier: float = 1.0  # 0.5 ~ 3.0
    unit_scale: float = 1.0  # 0.5 ~ 3.0

    # ── 帧率 ──
    target_fps: int = 60  # 15 / 30 / 60 / 120


class SettingsManager:
    """设置管理器.

    单例模式，从 %APPDATA%/DesktopBattle/settings.json 读取/保存设置。
    """

    _instance: SettingsManager | None = None

    def __init__(self) -> None:
        self._settings_path: Path = _get_settings_path()
        self.settings: RuntimeSettings = RuntimeSettings()
        self._modified: bool = False
        self.load()

    @classmethod
    def get_instance(cls) -> SettingsManager:
        """获取单例实例."""
        if cls._instance is None:
            cls._instance = SettingsManager()
        return cls._instance

    def load(self) -> None:
        """从磁盘加载设置."""
        try:
            if self._settings_path.exists():
                with open(self._settings_path, encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                self._apply_data(data)
        except (json.JSONDecodeError, OSError):
            pass  # 文件损坏或不存在时使用默认值

    def save(self) -> None:
        """保存设置到磁盘."""
        try:
            data = self._to_dict()
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._modified = False
        except OSError:
            pass

    def apply_to_config(self, game_config: object) -> None:
        """将运行时设置应用到 GameConfig.

        Args:
            game_config: GameConfig 实例
        """
        try:
            game_config.game_speed = self.settings.game_speed  # type: ignore[attr-defined]
            game_config.move_speed_multiplier = self.settings.move_speed_multiplier  # type: ignore[attr-defined]
            game_config.target_fps = self.settings.target_fps  # type: ignore[attr-defined]
        except AttributeError:
            pass

    def _to_dict(self) -> dict[str, Any]:
        """将设置序列化为字典."""
        return {
            "game_speed": self.settings.game_speed,
            "damage_multiplier": self.settings.damage_multiplier,
            "initial_units": self.settings.initial_units,
            "show_health_bars": self.settings.show_health_bars,
            "show_info_panel": self.settings.show_info_panel,
            "ai_enabled": self.settings.ai_enabled,
            "ai_api_url": self.settings.ai_api_url,
            "ai_api_key": self.settings.ai_api_key,
            "ai_model": self.settings.ai_model,
            "ai_interval": self.settings.ai_interval,
            "gravity": self.settings.gravity,
            "move_speed_multiplier": self.settings.move_speed_multiplier,
            "unit_scale": self.settings.unit_scale,
            "target_fps": self.settings.target_fps,
        }

    def _apply_data(self, data: dict[str, Any]) -> None:
        """从字典应用设置."""
        if "game_speed" in data:
            self.settings.game_speed = float(data["game_speed"])
        if "damage_multiplier" in data:
            self.settings.damage_multiplier = float(data["damage_multiplier"])
        if "initial_units" in data:
            self.settings.initial_units = int(data["initial_units"])
        if "show_health_bars" in data:
            self.settings.show_health_bars = bool(data["show_health_bars"])
        if "show_info_panel" in data:
            self.settings.show_info_panel = bool(data["show_info_panel"])
        if "ai_enabled" in data:
            self.settings.ai_enabled = bool(data["ai_enabled"])
        if "ai_api_url" in data:
            self.settings.ai_api_url = str(data["ai_api_url"])
        if "ai_api_key" in data:
            self.settings.ai_api_key = str(data["ai_api_key"])
        if "ai_model" in data:
            self.settings.ai_model = str(data["ai_model"])
        if "ai_interval" in data:
            self.settings.ai_interval = float(data["ai_interval"])
        if "gravity" in data:
            self.settings.gravity = float(data["gravity"])
        if "move_speed_multiplier" in data:
            self.settings.move_speed_multiplier = float(data["move_speed_multiplier"])
        if "unit_scale" in data:
            self.settings.unit_scale = float(data["unit_scale"])
        if "target_fps" in data:
            self.settings.target_fps = int(data["target_fps"])

    def set(self, key: str, value: Any) -> None:
        """修改单个设置项.

        Args:
            key: 设置键名
            value: 新值
        """
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self._modified = True

    def get(self, key: str, default: Any = None) -> Any:
        """获取单个设置项."""
        return getattr(self.settings, key, default)
