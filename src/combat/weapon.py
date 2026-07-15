"""Desktop Battle - 武器系统.

武器定义 (WeaponSpec) 与武器实例 (WeaponInstance)。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WeaponSpec:
    """武器规格定义 (不可变)."""

    name: str
    damage: float
    attack_range: float  # px
    attack_speed: float  # 攻击间隔 (秒)
    knockback: float
    damage_reduction: float = 0.0  # 减伤率 (0.0 ~ 1.0, 0=无减伤)
    crafting_cost_wood: int = 0
    crafting_cost_ore: int = 0
    crafting_station: str = "none"  # "none" | "workbench_lv1" | "workbench_lv2" | "workbench_lv3"
    crafting_time: float = 0.0  # 制作时间 (秒)
    visual_length: int = 5  # 视觉长度 (px)


# 预定义武器规格
WEAPON_SPECS: dict[str, WeaponSpec] = {
    "fist": WeaponSpec(
        name="徒手",
        damage=2.5,
        attack_range=10.0,
        attack_speed=1.5,
        knockback=50.0,
        damage_reduction=0.0,
        crafting_cost_wood=0,
        crafting_cost_ore=0,
        crafting_station="none",
        crafting_time=0.0,
        visual_length=0,
    ),
    "spear": WeaponSpec(
        name="长矛",
        damage=4.0,
        attack_range=22.0,
        attack_speed=2.0,
        knockback=100.0,
        damage_reduction=0.0,
        crafting_cost_wood=10,
        crafting_cost_ore=0,
        crafting_station="workbench_lv1",
        crafting_time=5.0,
        visual_length=8,
    ),
    "sword": WeaponSpec(
        name="剑",
        damage=6.0,
        attack_range=15.0,
        attack_speed=1.2,
        knockback=80.0,
        damage_reduction=0.0,
        crafting_cost_wood=5,
        crafting_cost_ore=8,
        crafting_station="workbench_lv2",
        crafting_time=8.0,
        visual_length=5,
    ),
    "shield": WeaponSpec(
        name="盾",
        damage=1.0,
        attack_range=8.0,
        attack_speed=2.0,
        knockback=150.0,
        damage_reduction=0.4,
        crafting_cost_wood=0,
        crafting_cost_ore=10,
        crafting_station="workbench_lv1",
        crafting_time=6.0,
        visual_length=3,
    ),
}


@dataclass
class WeaponInstance:
    """武器实例 (可掉落、可装备)."""

    spec: WeaponSpec
    weapon_id: int
    owner_id: int | None = None  # None = 在地面上

    # ── 生命周期 ──
    drop_time: float = 0.0
    max_drop_lifetime: float = 30.0

    # ── 位置 ──
    drop_x: float = 0.0
    drop_y: float = 0.0  # screen Y

    @property
    def is_on_ground(self) -> bool:
        return self.owner_id is None

    @property
    def expired(self) -> bool:
        return self.is_on_ground and self.drop_time > self.max_drop_lifetime

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def damage(self) -> float:
        return self.spec.damage

    @property
    def attack_range(self) -> float:
        return self.spec.attack_range

    @property
    def attack_speed(self) -> float:
        return self.spec.attack_speed

    @property
    def knockback(self) -> float:
        return self.spec.knockback

    @property
    def damage_reduction(self) -> float:
        return self.spec.damage_reduction

    def drop(self, x: float, y: float) -> None:
        """武器掉落到指定位置."""
        self.owner_id = None
        self.drop_x = x
        self.drop_y = y
        self.drop_time = 0.0

    def pickup(self, owner_id: int) -> None:
        """被拾取."""
        self.owner_id = owner_id
        self.drop_time = 0.0

    def update_lifetime(self, dt: float) -> None:
        """更新掉落计时."""
        if self.is_on_ground:
            self.drop_time += dt


def get_weapon_spec(weapon_name: str) -> WeaponSpec:
    """根据名称获取武器规格."""
    spec = WEAPON_SPECS.get(weapon_name)
    if spec is None:
        return WEAPON_SPECS["fist"]
    return spec


def can_craft_at_station(
    weapon_name: str,
    workbench_level: int,
) -> bool:
    """检查是否可以在指定等级的工具台制作武器."""
    spec = get_weapon_spec(weapon_name)
    if spec.crafting_station == "none":
        return False
    station_level = 0
    if spec.crafting_station == "workbench_lv1":
        station_level = 1
    elif spec.crafting_station == "workbench_lv2":
        station_level = 2
    elif spec.crafting_station == "workbench_lv3":
        station_level = 3
    return workbench_level >= station_level
