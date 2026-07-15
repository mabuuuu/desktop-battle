"""Desktop Battle - 全局配置 (Pydantic 模型).

所有可调参数集中管理，支持类型验证和默认值。
"""

from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """外部AI API配置."""

    enabled: bool = Field(default=False, description="是否启用AI策略")
    api_key: str = Field(default="", description="API密钥")
    api_url: str = Field(
        default="https://api.openai.com/v1/chat/completions",
        description="API端点(OpenAI兼容)",
    )
    model: str = Field(default="gpt-4o-mini", description="模型名称")
    strategy_interval: float = Field(default=15.0, description="策略请求间隔(秒)")
    max_tokens: int = Field(default=500, description="单次请求最大token")
    temperature: float = Field(default=0.7, description="生成温度")
    timeout: float = Field(default=10.0, description="请求超时(秒)")


class SchismConfig(BaseModel):
    """阵营分裂机制配置."""

    enabled: bool = Field(default=True, description="是否启用分裂机制")
    trigger_population: int = Field(default=15, description="触发矛盾积累的人口阈值")
    conflict_accumulate_interval: float = Field(default=5.0, description="矛盾积累间隔(秒)")
    conflict_base_rate: float = Field(default=1.0, description="每次基础矛盾增量")
    conflict_population_bonus: float = Field(default=0.5, description="每超1人额外增量")
    conflict_max: float = Field(default=100.0, description="矛盾值上限")
    schism_threshold: float = Field(default=80.0, description="分裂触发矛盾值")
    argue_threshold: float = Field(default=30.0, description="争吵触发矛盾值")
    skirmish_threshold: float = Field(default=60.0, description="小冲突触发矛盾值")
    argue_probability_per_second: float = Field(default=0.002, description="每秒每单位争吵概率系数")
    skirmish_probability_per_second: float = Field(default=0.005, description="每秒每单位小冲突概率系数")
    argue_duration_range: tuple[float, float] = Field(default=(1.0, 2.0), description="争吵持续秒数范围")
    skirmish_knockback: float = Field(default=20.0, description="小冲突击退力")
    resource_grab_probability: float = Field(default=0.6, description="资源点争夺成功概率")
    schism_cooldown: float = Field(default=120.0, description="分裂后冷却时间(秒)")
    split_ratio_range: tuple[float, float] = Field(default=(0.25, 0.50), description="分裂人数比例范围")
    rebel_initial_wood: int = Field(default=10, description="叛军初始木材")
    rebel_initial_ore: int = Field(default=5, description="叛军初始矿石")


class FactionConfig(BaseModel):
    """阵营配置."""

    name: str = Field(description="阵营名称")
    color_hex: str = Field(description="阵营主色(HEX, 如 #FF4444)")
    secondary_color_hex: str = Field(description="阵营辅色(HEX, 如 #FF8866)")
    initial_wood: int = Field(default=30, description="初始木材")
    initial_ore: int = Field(default=15, description="初始矿石")
    initial_units: int = Field(default=5, description="初始单位数")
    max_units: int = Field(default=30, description="最大单位数")
    unit_hp: int = Field(default=1000, description="单位HP")
    move_speed: float = Field(default=60.0, description="移动速度(px/s)")
    climb_speed: float = Field(default=40.0, description="攀爬速度(px/s)")
    fist_damage: float = Field(default=2.5, description="徒手伤害(取均值)")
    gather_speed: float = Field(default=5.0, description="采集速度(资源/秒)")


class GameConfig(BaseModel):
    """全局游戏配置."""

    # ── 帧率与时间 ──
    target_fps: int = Field(default=60, description="目标帧率")
    physics_dt: float = Field(default=1.0 / 60.0, description="物理步长(秒)")
    behavior_tick_interval: int = Field(
        default=3, description="行为树每N帧tick一次(20Hz)"
    )

    # ── 物理引擎 ──
    gravity: float = Field(default=900.0, description="重力加速度(px/s²)")
    damping: float = Field(default=0.9, description="全局速度阻尼")
    collision_slop: float = Field(default=0.5, description="碰撞穿透容差")
    physics_iterations: int = Field(default=10, description="约束求解迭代次数")

    # ── 单位通用属性 ──
    unit_perception_range: float = Field(default=100.0, description="感知范围(px)")
    unit_carry_capacity: int = Field(default=20, description="单次采集最大携带量")
    unit_radius: float = Field(default=2.0, description="碰撞体半径(px)")
    unit_mass: float = Field(default=1.0, description="单位质量")
    unit_friction: float = Field(default=0.6, description="单位摩擦系数")
    unit_elasticity: float = Field(default=0.1, description="单位弹性系数")

    # ── 火柴人渲染 ──
    stickman_height: int = Field(default=20, description="火柴人总高度(px)")
    stickman_line_width: int = Field(default=1, description="火柴人线宽(px)")
    stickman_head_radius: int = Field(default=2, description="火柴人头部半径(px)")

    # ── 资源 ──
    resource_output_rate: float = Field(default=5.0, description="采集点产率(资源/秒)")

    # ── 兵营 ──
    barracks_production_interval: float = Field(
        default=30.0, description="兵营生产间隔(秒)"
    )
    barracks_production_cost_wood: int = Field(
        default=5, description="兵营生产单位木材消耗"
    )
    barracks_production_cost_ore: int = Field(
        default=3, description="兵营生产单位矿石消耗"
    )
    barracks_max_queue: int = Field(default=5, description="兵营最大生产队列")
    max_barracks_per_faction: int = Field(default=3, description="每阵营最大兵营数")

    # ── 桌面扫描 ──
    window_scan_interval: float = Field(
        default=2.0, description="窗口扫描间隔(秒)"
    )

    # ── 武器 ──
    weapon_drop_lifetime: float = Field(default=30.0, description="掉落武器存活时间(秒)")

    # ── 其他 ──
    game_speed: float = Field(default=1.0, description="游戏速度倍率")
    terrain_friction: float = Field(default=0.8, description="地形摩擦系数")
    terrain_elasticity: float = Field(default=0.1, description="地形弹性系数")
    building_spacing: int = Field(default=10, description="建筑最小间距(px)")
    max_unit_fall_speed: float = Field(default=500.0, description="最大下落速度(px/s)")

    # ── 阵营 ──
    factions: list[FactionConfig] = Field(
        default_factory=lambda: [
            FactionConfig(
                name="红方",
                color_hex="#FF4444",
                secondary_color_hex="#FF8866",
                move_speed=65.0,
                fist_damage=3.0,
                gather_speed=4.5,
            ),
            FactionConfig(
                name="蓝方",
                color_hex="#4488FF",
                secondary_color_hex="#66AAFF",
                unit_hp=1050,
                move_speed=60.0,
                fist_damage=2.0,
                gather_speed=5.5,
            ),
        ],
        description="阵营配置列表",
    )

    # ── AI ──
    ai: AIConfig = Field(default_factory=AIConfig, description="AI配置")

    # ── 分裂 ──
    schism: SchismConfig = Field(default_factory=SchismConfig, description="分裂机制配置")

    @staticmethod
    def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
        """将 HEX 颜色(#RRGGBB)转换为 RGBA 元组."""
        hex_str = hex_color.lstrip("#")
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (r, g, b, alpha)

    def get_faction_by_name(self, name: str) -> FactionConfig:
        """根据名称获取阵营配置."""
        for f in self.factions:
            if f.name == name:
                return f
        raise ValueError(f"未找到阵营: {name}")
