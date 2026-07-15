"""Desktop Battle - AI 策略提示词模板.

内置系统提示词和用户消息模板，将当前战况转换为 JSON 策略。
"""

from __future__ import annotations

SYSTEM_PROMPT: str = """You are a battle strategist for "Desktop Battle", a real-time desktop stickman war game.

Two factions fight on the Windows desktop. Each faction has units, buildings, resources, and weapons.

Available strategy types: "expand" (grow economy), "rush" (attack early), "defense" (build defenses), "tech" (research better weapons).

Available unit roles: gatherer (collect resources), builder (construct buildings), soldier (fight enemies), scout (explore).

You must output ONLY a valid JSON object with this structure:
{
  "strategy": "expand" | "rush" | "defense" | "tech",
  "reasoning": "Brief explanation of your decision (max 50 words)",
  "build_orders": [
    {"type": "workbench" | "barracks", "level": 1 | 2 | 3, "priority": 1 | 2 | 3}
  ],
  "craft_orders": [
    {"weapon": "spear" | "sword" | "shield", "count": number}
  ],
  "role_allocation": {
    "gatherers": number,
    "builders": number,
    "soldiers": number,
    "scouts": number
  },
  "rally_point": "left" | "right" | "center",
  "aggression": number from 0.0 to 1.0
}

Rules:
- Total role_allocation should not exceed current alive unit count
- Build orders require available resources
- Craft orders require appropriate workbench level
- Be aggressive when you have more units, defensive when fewer
- Prioritize economy early game (wood/ore income)
"""


def build_user_message(
    faction_name: str,
    alive_units: int,
    total_units: int,
    dead_units: int,
    wood: int,
    ore: int,
    workbench_level: int,
    barracks_count: int,
    weapons_count: int,
    enemy_name: str,
    enemy_alive: int,
    enemy_dead: int,
    threat_level: float,
    elapsed_time: float,
    current_strategy: str,
    units_produced: int,
    units_lost: int,
) -> str:
    """构建发送给 AI 的用户消息 (战况报告).

    Args:
        faction_name: 本方阵营名
        alive_units: 存活单位数
        total_units: 总单位数(含死亡)
        dead_units: 阵亡单位数
        wood: 木材
        ore: 矿石
        workbench_level: 最高工具台等级
        barracks_count: 兵营数
        weapons_count: 已装备武器数
        enemy_name: 敌方阵营名
        enemy_alive: 敌方存活单位数
        enemy_dead: 敌方阵亡数
        threat_level: 威胁等级 (0-1)
        elapsed_time: 游戏时间 (秒)
        current_strategy: 当前策略
        units_produced: 已生产单位数
        units_lost: 阵亡单位数

    Returns:
        战况报告消息字符串
    """
    mins = int(elapsed_time // 60)
    secs = int(elapsed_time % 60)

    return f"""Current Battle Status:

=== YOUR FACTION: {faction_name} ===
- Units: {alive_units} alive / {total_units} total ({dead_units} dead)
- Units Produced: {units_produced} / Lost: {units_lost}
- Resources: Wood={wood}, Ore={ore}
- Buildings: Workbench Lv{workbench_level}, Barracks={barracks_count}
- Armed Units: {weapons_count}
- Current Strategy: {current_strategy}

=== ENEMY: {enemy_name} ===
- Enemy Units Alive: {enemy_alive}
- Enemy Dead: {enemy_dead}
- Threat Level: {threat_level:.2f} (0=safe, 1=critical)

=== GAME TIME ===
- {mins:02d}:{secs:02d}

Based on this battle status, what strategy should we adopt? Provide your recommendation as a JSON object."""


def build_strategy_summary(
    strategy: dict,
    faction_name: str,
) -> str:
    """从策略 JSON 生成可读摘要.

    Args:
        strategy: AI 返回的策略 JSON
        faction_name: 阵营名

    Returns:
        策略摘要字符串
    """
    strat_type = strategy.get("strategy", "unknown")
    reasoning = strategy.get("reasoning", "No reasoning provided")
    aggression = strategy.get("aggression", 0.5)
    roles = strategy.get("role_allocation", {})
    builds = strategy.get("build_orders", [])
    crafts = strategy.get("craft_orders", [])

    parts = [
        f"[{faction_name}] Strategy: {strat_type} (aggression: {aggression:.1f})",
        f"  Reason: {reasoning}",
        f"  Roles: G={roles.get('gatherers', 0)} B={roles.get('builders', 0)} "
        f"S={roles.get('soldiers', 0)} Sc={roles.get('scouts', 0)}",
    ]

    for b in builds:
        parts.append(f"  Build: {b.get('type')} Lv{b.get('level')} (priority {b.get('priority')})")
    for c in crafts:
        parts.append(f"  Craft: {c.get('weapon')} x{c.get('count')}")

    return "\n".join(parts)
