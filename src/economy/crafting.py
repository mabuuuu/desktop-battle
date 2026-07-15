"""Desktop Battle - 制作系统.

在工具台旁制作武器：扣除资源、制作计时、武器出现。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.combat.weapon import WeaponInstance, WeaponSpec
    from src.entity.faction import Faction
    from src.entity.unit import Unit


@dataclass
class CraftingJob:
    """制作任务."""

    weapon_name: str
    progress: float = 0.0
    total_time: float = 0.0
    crafter_id: int | None = None
    done: bool = False

    def update(self, dt: float) -> None:
        """更新制作进度."""
        if not self.done:
            self.progress += dt
            if self.progress >= self.total_time:
                self.progress = self.total_time
                self.done = True




class CraftingManager:
    """制作管理器."""

    def __init__(self) -> None:
        self._pending_jobs: list[CraftingJob] = []

    def start_craft(
        self,
        weapon_name: str,
        faction: Faction,
        unit: Unit,
    ) -> CraftingJob | None:
        """开始制作武器.

        Args:
            weapon_name: 武器名称 (如 "spear", "sword", "shield")
            faction: 所属阵营 (扣除资源)
            unit: 制作单位

        Returns:
            制作任务 (None 表示资源不足或无法制作)
        """
        from src.combat.weapon import can_craft_at_station, get_weapon_spec

        spec = get_weapon_spec(weapon_name)
        if spec.crafting_station == "none":
            return None

        # 检查工具台等级
        workbench_level = faction.get_workbench_highest_level()
        if not can_craft_at_station(weapon_name, workbench_level):
            return None

        # 检查资源
        if not faction.can_afford(spec.crafting_cost_wood, spec.crafting_cost_ore):
            return None

        # 扣除资源
        if not faction.spend(spec.crafting_cost_wood, spec.crafting_cost_ore):
            return None

        # 创建制作任务
        job = CraftingJob(
            weapon_name=weapon_name,
            progress=0.0,
            total_time=spec.crafting_time,
            crafter_id=unit.unit_id,
        )
        self._pending_jobs.append(job)
        return job

    def update(self, dt: float) -> list[CraftingJob]:
        """更新所有制作进度，返回已完成的制作任务."""
        completed: list[CraftingJob] = []
        for job in self._pending_jobs:
            if not job.done:
                job.update(dt)
                if job.done:
                    completed.append(job)

        # 清理已完成任务
        self._pending_jobs = [j for j in self._pending_jobs if not j.done]
        return completed

    def get_pending_count(self) -> int:
        """获取待处理制作数."""
        return len(self._pending_jobs)
