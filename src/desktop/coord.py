"""Desktop Battle - 屏幕/物理坐标转换.

pymunk 使用 Y 轴向上的坐标系，屏幕使用 Y 轴向下的坐标系。
"""


def physics_to_screen(
    phys_x: float, phys_y: float, screen_height: int
) -> tuple[float, float]:
    """将 pymunk 坐标 (Y轴向上) 转换为屏幕坐标 (Y轴向下)."""
    return (phys_x, float(screen_height) - phys_y)


def screen_to_physics(
    screen_x: float, screen_y: float, screen_height: int
) -> tuple[float, float]:
    """将屏幕坐标 (Y轴向下) 转换为 pymunk 坐标 (Y轴向上)."""
    return (screen_x, float(screen_height) - screen_y)
