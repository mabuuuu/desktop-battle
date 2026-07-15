"""Desktop Battle - AI 策略管理器.

每15秒请求 AI 获取策略建议，JSON 解析后写入 FactionBlackboard。
支持降级策略: 连续3次失败后切换到内置规则策略。
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from src.ai.client import AIClient
    from src.behavior.blackboard import FactionBlackboard
    from src.core.world import World
    from src.entity.faction import Faction


class AIStrategyManager:
    """AI 策略管理器.

    为每个阵营管理 AI 策略请求、解析和应用。
    """

    def __init__(
        self,
        world: World,
        api_key: str = "",
        api_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-4o-mini",
        interval: float = 15.0,
        timeout: float = 10.0,
    ) -> None:
        self._world: World = world
        self._interval: float = interval
        self._enabled: bool = bool(api_key)

        # 每个阵营的计时器
        self._faction_timers: dict[str, float] = {}
        self._faction_fail_counts: dict[str, int] = {}

        # AI 客户端
        if self._enabled:
            from src.ai.client import AIClient
            self._client: AIClient | None = AIClient(
                api_key=api_key,
                api_url=api_url,
                model=model,
                timeout=timeout,
            )
        else:
            self._client = None

        # 阵营黑板映射 (由外部设置)
        self._faction_blackboards: dict[str, FactionBlackboard] = {}

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_blackboard(self, faction_name: str, bb: FactionBlackboard) -> None:
        """为阵营设置黑板."""
        self._faction_blackboards[faction_name] = bb

    def update(self, dt: float) -> None:
        """更新策略管理器，触发定期AI请求.

        Args:
            dt: 时间步长
        """
        if not self._enabled:
            # 使用内置规则策略
            for faction in self._world.factions:
                self._apply_rules_strategy(faction)
            return

        for faction in self._world.factions:
            name = faction.name
            self._faction_timers.setdefault(name, 0.0)
            self._faction_fail_counts.setdefault(name, 0)
            self._faction_timers[name] += dt

            if self._faction_timers[name] >= self._interval:
                self._faction_timers[name] = 0.0

                # 检查降级策略
                if self._faction_fail_counts[name] >= 3:
                    logger.warning(f"AI fallback to rules for {name}")
                    self._apply_rules_strategy(faction)
                    continue

                # 请求 AI 策略
                try:
                    self._request_ai_strategy(faction)
                    self._faction_fail_counts[name] = 0
                except Exception as e:
                    logger.error(f"AI strategy request failed for {name}: {e}")
                    self._faction_fail_counts[name] += 1
                    if self._faction_fail_counts[name] >= 3:
                        logger.warning(f"AI permanently fallback for {name}")
                    self._apply_rules_strategy(faction)

    def _request_ai_strategy(self, faction: Faction) -> None:
        """向AI请求策略并应用到黑板.

        Args:
            faction: 阵营
        """
        if self._client is None:
            return

        # 获取敌方信息
        enemy_faction = None
        for f in self._world.factions:
            if f.name != faction.name:
                enemy_faction = f
                break

        if enemy_faction is None:
            return

        from src.ai.prompts import SYSTEM_PROMPT, build_user_message

        # 构建战况消息
        user_msg = build_user_message(
            faction_name=faction.name,
            alive_units=faction.alive_count,
            total_units=len(faction.units),
            dead_units=faction.dead_units,
            wood=faction.wood,
            ore=faction.ore,
            workbench_level=faction.get_workbench_highest_level(),
            barracks_count=faction.get_barracks_count(),
            weapons_count=sum(1 for u in faction.alive_units if u.weapon is not None),
            enemy_name=enemy_faction.name,
            enemy_alive=enemy_faction.alive_count,
            enemy_dead=enemy_faction.dead_units,
            threat_level=self._calculate_threat(faction, enemy_faction),
            elapsed_time=self._world.elapsed_time,
            current_strategy=faction.current_strategy,
            units_produced=faction.units_produced,
            units_lost=faction.units_lost,
        )

        # 发送请求
        strategy = self._client.send_strategy_request(SYSTEM_PROMPT, user_msg)

        # 解析并应用
        self._apply_strategy(faction, strategy)

        # 记录
        from src.ai.strategy_log import log_strategy_response
        log_strategy_response(faction.name, strategy)

    def _apply_strategy(self, faction: Faction, strategy: dict) -> None:
        """将AI策略写入阵营黑板.

        Args:
            faction: 阵营
            strategy: AI 返回的策略 JSON
        """
        bb = self._faction_blackboards.get(faction.name)
        if bb is None:
            return

        # 更新策略
        strat_type = strategy.get("strategy", "expand")
        faction.current_strategy = str(strat_type)
        bb.current_strategy = str(strat_type)

        # 威胁级别
        aggression = float(strategy.get("aggression", 0.5))
        bb.threat_level = aggression

        # 角色分配
        roles = strategy.get("role_allocation", {})
        bb.gatherers_needed = int(roles.get("gatherers", 2))
        bb.builders_needed = int(roles.get("builders", 1))
        bb.soldiers_needed = int(roles.get("soldiers", 2))
        bb.scouts_needed = int(roles.get("scouts", 0))

        # 建造订单
        build_orders = strategy.get("build_orders", [])
        for bo in build_orders:
            btype = str(bo.get("type", ""))
            level = int(bo.get("level", 1))
            if btype in ("workbench", "barracks"):
                # 在阵营出生点附近放置建造点
                bb.add_build_order(btype, level, faction.spawn_x + 50, faction.spawn_y)

        # 制作订单
        craft_orders = strategy.get("craft_orders", [])
        for co in craft_orders:
            weapon = str(co.get("weapon", ""))
            count = int(co.get("count", 0))
            benches = faction.get_buildings_by_type("workbench")
            if benches and weapon in ("spear", "sword", "shield") and count > 0:
                for _ in range(min(count, 3)):
                    bb.add_craft_order(weapon, benches[0].building_id)

    def _apply_rules_strategy(self, faction: Faction) -> None:
        """内置规则策略 (AI不可用时的降级方案).

        Args:
            faction: 阵营
        """
        bb = self._faction_blackboards.get(faction.name)
        if bb is None:
            return

        alive = faction.alive_count
        wood = faction.wood
        ore = faction.ore
        bench_level = faction.get_workbench_highest_level()
        barracks_count = faction.get_barracks_count()

        # 简单规则:
        # 1. 少于3单位 → 防守
        # 2. 资源充足 → 扩展/科技
        # 3. 单位优势 → 进攻

        enemy_faction = None
        for f in self._world.factions:
            if f.name != faction.name:
                enemy_faction = f
                break

        enemy_alive = enemy_faction.alive_count if enemy_faction else 0

        if alive < 3:
            bb.current_strategy = "defense"
            bb.threat_level = 1.0
            bb.gatherers_needed = max(1, alive)
            bb.builders_needed = 0
            bb.soldiers_needed = 0
            bb.scouts_needed = 0
        elif alive > enemy_alive + 2:
            bb.current_strategy = "rush"
            bb.threat_level = 0.8
            bb.gatherers_needed = max(1, alive // 4)
            bb.builders_needed = 1
            bb.soldiers_needed = alive - 2
            bb.scouts_needed = 0
        elif wood >= 30 and ore >= 20 and bench_level < 3:
            bb.current_strategy = "tech"
            bb.threat_level = 0.3
            bb.gatherers_needed = max(1, alive // 3)
            bb.builders_needed = 2
            bb.soldiers_needed = alive - 3
            bb.scouts_needed = 0
        else:
            bb.current_strategy = "expand"
            bb.threat_level = 0.5
            bb.gatherers_needed = max(1, alive // 2)
            bb.builders_needed = 1
            bb.soldiers_needed = max(1, alive - 3)
            bb.scouts_needed = 0

        faction.current_strategy = bb.current_strategy

        # 自动建造
        if bench_level == 0 and wood >= 15:
            bb.add_build_order("workbench", 1, faction.spawn_x + 50, faction.spawn_y)
        elif bench_level == 1 and wood >= 15 and ore >= 10:
            bb.add_build_order("workbench", 2, faction.spawn_x + 70, faction.spawn_y)
        elif barracks_count == 0 and wood >= 20 and alive >= 4:
            bb.add_build_order("barracks", 1, faction.spawn_x - 50, faction.spawn_y)

        # 自动制作
        if bench_level >= 1 and wood >= 10 and ore >= 8:
            benches = faction.get_buildings_by_type("workbench")
            if benches:
                bb.add_craft_order("spear", benches[0].building_id)
        if bench_level >= 2 and wood >= 5 and ore >= 15:
            benches = faction.get_buildings_by_type("workbench")
            if benches:
                bb.add_craft_order("sword", benches[0].building_id)
                bb.add_craft_order("shield", benches[0].building_id)

    @staticmethod
    def _calculate_threat(faction: Faction, enemy: Faction) -> float:
        """计算威胁等级 (0~1).

        Args:
            faction: 本方
            enemy: 敌方

        Returns:
            威胁等级
        """
        if enemy.alive_count == 0:
            return 0.0
        if faction.alive_count == 0:
            return 1.0
        ratio = float(enemy.alive_count) / float(faction.alive_count)
        return min(1.0, ratio * 0.7)
