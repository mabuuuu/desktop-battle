"""Desktop Battle - 精灵绘制工具.

所有绘制函数操作 numpy RGBA 数组 (height, width, 4)，不依赖任何图形库。
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np


def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    """将 HEX 颜色字符串 (#RRGGBB) 转换为 RGBA 元组."""
    hex_str = hex_color.lstrip("#")
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
        alpha,
    )


def draw_pixel(
    buffer: np.ndarray,
    x: int,
    y: int,
    color: tuple[int, int, int, int],
) -> None:
    """在 buffer 上绘制单个像素（带边界检查）."""
    h, w = buffer.shape[0], buffer.shape[1]
    if 0 <= x < w and 0 <= y < h:
        buffer[y, x] = color


def draw_line(
    buffer: np.ndarray,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: tuple[int, int, int, int],
    thickness: int = 1,
) -> None:
    """Bresenham 直线绘制 (支持粗细)."""
    if thickness <= 0:
        return
    h, w = buffer.shape[0], buffer.shape[1]

    ix1, iy1 = int(round(x1)), int(round(y1))
    ix2, iy2 = int(round(x2)), int(round(y2))

    dx = abs(ix2 - ix1)
    dy = -abs(iy2 - iy1)
    sx = 1 if ix1 < ix2 else -1
    sy = 1 if iy1 < iy2 else -1
    err = dx + dy

    half = thickness // 2

    while True:
        # 对于线宽 > 1，绘制一个小的填充方块
        for ty in range(-half, thickness - half):
            for tx in range(-half, thickness - half):
                px, py = ix1 + tx, iy1 + ty
                if 0 <= px < w and 0 <= py < h:
                    buffer[py, px] = color

        if ix1 == ix2 and iy1 == iy2:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            ix1 += sx
        if e2 <= dx:
            err += dx
            iy1 += sy


def draw_circle(
    buffer: np.ndarray,
    cx: float,
    cy: float,
    radius: int,
    color: tuple[int, int, int, int],
    thickness: int = 0,
) -> None:
    """Midpoint circle algorithm 绘制圆/填充圆."""
    if radius < 0:
        return
    h, w = buffer.shape[0], buffer.shape[1]
    icx, icy = int(round(cx)), int(round(cy))

    if thickness <= 0:
        # 填充圆
        for y in range(max(0, icy - radius), min(h, icy + radius + 1)):
            for x in range(max(0, icx - radius), min(w, icx + radius + 1)):
                if (x - icx) ** 2 + (y - icy) ** 2 <= radius**2:
                    buffer[y, x] = color
    else:
        # 空心圆
        x = radius
        y = 0
        err = 0
        while x >= y:
            _thick_pixels(buffer, icx + x, icy + y, color, thickness, w, h)
            _thick_pixels(buffer, icx + y, icy + x, color, thickness, w, h)
            _thick_pixels(buffer, icx - y, icy + x, color, thickness, w, h)
            _thick_pixels(buffer, icx - x, icy + y, color, thickness, w, h)
            _thick_pixels(buffer, icx - x, icy - y, color, thickness, w, h)
            _thick_pixels(buffer, icx - y, icy - x, color, thickness, w, h)
            _thick_pixels(buffer, icx + y, icy - x, color, thickness, w, h)
            _thick_pixels(buffer, icx + x, icy - y, color, thickness, w, h)

            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x


def _thick_pixels(
    buffer: np.ndarray,
    cx: int,
    cy: int,
    color: tuple[int, int, int, int],
    thickness: int,
    w: int,
    h: int,
) -> None:
    """在 (cx, cy) 周围绘制 thickness 大小的像素块."""
    half = thickness // 2
    for dy in range(-half, thickness - half):
        for dx in range(-half, thickness - half):
            px, py = cx + dx, cy + dy
            if 0 <= px < w and 0 <= py < h:
                buffer[py, px] = color


def draw_rect(
    buffer: np.ndarray,
    x: float,
    y: float,
    width: int,
    height: int,
    color: tuple[int, int, int, int],
    thickness: int = 0,
) -> None:
    """绘制矩形 (空心 / 填充)."""
    h, w = buffer.shape[0], buffer.shape[1]
    ix, iy = int(round(x)), int(round(y))

    if thickness <= 0:
        # 填充矩形
        for py in range(max(0, iy), min(h, iy + height)):
            for px in range(max(0, ix), min(w, ix + width)):
                buffer[py, px] = color
    else:
        # 四条边
        # 上边
        for py in range(iy, min(iy + thickness, h)):
            for px in range(max(0, ix), min(w, ix + width)):
                buffer[py, px] = color
        # 下边
        for py in range(max(iy + height - thickness, 0), min(iy + height, h)):
            for px in range(max(0, ix), min(w, ix + width)):
                buffer[py, px] = color
        # 左边
        for py in range(max(0, iy), min(iy + height, h)):
            for px in range(ix, min(ix + thickness, w)):
                buffer[py, px] = color
        # 右边
        for py in range(max(0, iy), min(iy + height, h)):
            for px in range(max(ix + width - thickness, 0), min(ix + width, w)):
                buffer[py, px] = color


def draw_text(
    buffer: np.ndarray,
    x: float,
    y: float,
    text: str,
    color: tuple[int, int, int, int],
    font_size: int = 12,
) -> None:
    """简易位图文本绘制 (ASCII 5x7 字体).

    仅支持 ASCII 可打印字符。位置 (x, y) 为文本左上角。
    """
    # 简易 5x7 像素字体 — 仅覆盖常用字符
    glyphs: dict[str, list[list[int]]] = {
        "0": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "1": [
            [0, 1, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 1],
        ],
        "2": [
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
        ],
        "3": [
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
        "4": [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
        ],
        "5": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
        "6": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "7": [
            [1, 1, 1],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
        ],
        "8": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "9": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
        "A": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
        ],
        "B": [
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
        ],
        "C": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 1, 1],
        ],
        "D": [
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 0],
        ],
        "E": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
        ],
        "F": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
        ],
        "G": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "H": [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
        ],
        "I": [[1, 1, 1], [0, 1, 0], [0, 1, 0], [0, 1, 0], [1, 1, 1]],
        "J": [
            [0, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "K": [
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 0],
            [1, 1, 0],
            [1, 0, 1],
        ],
        "L": [
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 1, 1],
        ],
        "M": [
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
        ],
        "N": [
            [1, 0, 1],
            [1, 1, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
        ],
        "O": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "P": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
        ],
        "Q": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 0],
            [0, 1, 1],
        ],
        "R": [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
        ],
        "S": [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
        "T": [[1, 1, 1], [0, 1, 0], [0, 1, 0], [0, 1, 0], [0, 1, 0]],
        "U": [
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        "V": [
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 1, 0],
        ],
        "W": [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 1, 1],
            [1, 0, 1],
        ],
        "X": [
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
        ],
        "Y": [
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ],
        "Z": [
            [1, 1, 1],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 1, 1],
        ],
        " ": [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]],
        ":": [[0], [1], [0], [1], [0]],
        "/": [
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
        ],
        ".": [[0], [0], [0], [0], [1]],
        ",": [[0], [0], [0], [1], [1]],
        "-": [[0, 0, 0], [0, 0, 0], [1, 1, 1], [0, 0, 0], [0, 0, 0]],
        "+": [
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
        ],
        "(": [[0, 1], [1, 0], [1, 0], [1, 0], [0, 1]],
        ")": [[1, 0], [0, 1], [0, 1], [0, 1], [1, 0]],
        "%": [
            [1, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 1],
        ],
        "×": [
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [0, 0, 0],
            [0, 0, 0],
        ],
    }

    scale = max(1, font_size // 8)
    glyph_w = 3 * scale + scale
    glyph_h = 5 * scale + scale

    ix, iy = int(round(x)), int(round(y))
    for char_idx, ch in enumerate(text):
        upper = ch.upper() if ch.isalpha() else ch
        glyph = glyphs.get(upper, glyphs.get(" ", [[0]]))
        for gy, row in enumerate(glyph):
            if gy >= len(glyph):
                break
            for gx, pixel_val in enumerate(row):
                if pixel_val:
                    for sy in range(scale):
                        for sx in range(scale):
                            draw_pixel(
                                buffer,
                                ix + char_idx * glyph_w + gx * scale + sx,
                                iy + gy * scale + sy,
                                color,
                            )
                    # Also draw at original positions without scaling for small size
                    if scale <= 1:
                        draw_pixel(
                            buffer,
                            ix + char_idx * 4 + gx,
                            iy + gy,
                            color,
                        )


def draw_stickman(
    buffer: np.ndarray,
    body_screen_x: float,
    body_screen_y: float,
    faction_color: tuple[int, int, int, int],
    secondary_color: tuple[int, int, int, int],
    line_width: int = 1,
    head_radius: int = 2,
    state: str = "idle",
    anim_frame: int = 0,
    weapon_visual: tuple[str, int] | None = None,
    facing_right: bool = True,
) -> None:
    """在 RGBA buffer 上绘制火柴人.

    以 (body_screen_x, body_screen_y) 为脚底锚点:
    - 身体从 (0, -16) 画到 (0, -8)——即从脚底向上 8~16px
    - 头在 (0, -18)，半径 head_radius (2)
    - 手臂从 (0, -14) 出发
    - 腿从 (0, -8) 出发画到 (0, 0)

    实际: 以 body_screen_y 为 Y=0（脚底），向上为负。
    """
    import math as _math

    # 火柴人局部坐标（屏幕Y向下，所以"上"是负Y）
    fx = body_screen_x
    fy = body_screen_y  # 脚底

    dir_sign = 1 if facing_right else -1

    # 身体线段: 脚底上方 8px 到 16px（总长 8px，即身体从(0, -16)到(0, -8)）
    body_top_y = fy - 16
    body_bottom_y = fy - 8

    # 头位置
    head_y = fy - 18

    # 手臂根位置
    arm_root_y = fy - 14

    # idle 呼吸微动
    breath_offset = 0.5 if (anim_frame % 30) < 15 else 0.0

    # walking: 腿臂交替
    walk_swing = 0.0
    if state == "walking":
        walk_phase = (anim_frame % 20) / 20.0
        walk_swing = _math.sin(walk_phase * _math.pi * 2) * 2.0

    # mining: 手臂向下挥
    mining_angle = 0.0
    if state == "mining":
        mining_phase = (anim_frame % 18) / 18.0
        mining_angle = _math.sin(mining_phase * _math.pi) * 0.6

    # attacking: 手臂向前挥
    attack_offset = 0.0
    if state == "attacking":
        attack_phase = (anim_frame % 12) / 12.0
        if attack_phase < 0.5:
            attack_offset = attack_phase * 6
        else:
            attack_offset = (1.0 - attack_phase) * 6

    # fighting: 战斗姿态 (警戒，略微下蹲)
    fight_stance = 0.0
    if state == "fighting":
        fight_stance = 1.5
        attack_phase = (anim_frame % 15) / 15.0
        if attack_phase < 0.5:
            attack_offset = attack_phase * 5
        else:
            attack_offset = (1.0 - attack_phase) * 5

    # climbing: 攀爬姿态 (双臂上举，身体垂直)
    if state == "climbing":
        climb_phase = (anim_frame % 16) / 16.0
        climb_offset = _math.sin(climb_phase * _math.pi * 2) * 1.0

    # fleeing: 逃跑姿态 (身体前倾)
    flee_offset = 0.0
    if state == "fleeing":
        flee_offset = 2.0

    # building: 建造姿态 (手臂在身前)
    build_offset = 0.0
    if state == "building":
        build_phase = (anim_frame % 20) / 20.0
        build_offset = _math.sin(build_phase * _math.pi) * 1.5

    # crafting: 制作姿态 (手臂小幅动作)
    craft_offset = 0.0
    if state == "crafting":
        craft_phase = (anim_frame % 24) / 24.0
        craft_offset = _math.sin(craft_phase * _math.pi * 2) * 0.75

    # dying: 倒下动画
    dying_fall = 0.0
    if state == "dying":
        dying_fall = min(10.0, (anim_frame % 20) * 0.5)

    # carrying: 搬运姿态 (手臂下垂)
    carry_offset = 0.0
    if state == "carrying":
        carry_offset = 1.0

    # arguing: 争吵姿态 (面对面对峙)
    argue_offset = 0.0
    if state == "arguing":
        argue_offset = 1.5

    # 身体 (带各状态偏移)
    body_shift_y = 0.0
    if state == "fighting":
        body_shift_y = fight_stance
    elif state == "fleeing":
        body_shift_y = flee_offset
    elif state == "dying":
        body_shift_y = dying_fall
    elif state == "arguing":
        body_shift_y = argue_offset

    draw_line(
        buffer,
        fx,
        body_top_y + breath_offset + body_shift_y,
        fx,
        body_bottom_y + breath_offset + body_shift_y,
        faction_color,
        line_width,
    )

    # 腿
    if state == "dying":
        # 倒下: 腿水平伸展
        left_leg_end_x = fx - 5 * dir_sign
        left_leg_end_y = body_bottom_y + breath_offset + body_shift_y + 4
        right_leg_end_x = fx + 1 * dir_sign
        right_leg_end_y = body_bottom_y + breath_offset + body_shift_y + 3
        draw_line(
            buffer, fx, body_bottom_y + breath_offset + body_shift_y,
            left_leg_end_x, left_leg_end_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, body_bottom_y + breath_offset + body_shift_y,
            right_leg_end_x, right_leg_end_y, faction_color, line_width
        )
    else:
        left_leg_end_x = fx - 3 * dir_sign + walk_swing * dir_sign
        right_leg_end_x = fx + 3 * dir_sign - walk_swing * dir_sign
        draw_line(
            buffer, fx, body_bottom_y + breath_offset + body_shift_y,
            left_leg_end_x, fy, faction_color, line_width
        )
        draw_line(
            buffer, fx, body_bottom_y + breath_offset + body_shift_y,
            right_leg_end_x, fy, faction_color, line_width
        )

    # 手臂
    if state == "climbing":
        # 攀爬: 双手上举
        left_arm_x = fx - 2
        left_arm_y = body_top_y + breath_offset - 3 + climb_offset
        right_arm_x = fx + 2
        right_arm_y = body_top_y + breath_offset - 3 - climb_offset
        draw_line(
            buffer, fx, arm_root_y + breath_offset, left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset, right_arm_x, right_arm_y, faction_color, line_width
        )
    elif state == "building":
        # 建造: 手臂在身前水平
        left_arm_x = fx - 4 * dir_sign + build_offset
        left_arm_y = arm_root_y + 2 + breath_offset
        right_arm_x = fx + 1.5 * dir_sign - build_offset
        right_arm_y = arm_root_y + 2 + breath_offset
        draw_line(
            buffer, fx, arm_root_y + breath_offset, left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset, right_arm_x, right_arm_y, faction_color, line_width
        )
    elif state == "crafting":
        # 制作: 双手小幅动作
        left_arm_x = fx - 3 + craft_offset
        left_arm_y = arm_root_y + 3 + breath_offset
        right_arm_x = fx + 3 - craft_offset
        right_arm_y = arm_root_y + 3 + breath_offset
        draw_line(
            buffer, fx, arm_root_y + breath_offset, left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset, right_arm_x, right_arm_y, faction_color, line_width
        )
    elif state == "carrying":
        # 搬运: 手臂自然下垂
        left_arm_x = fx - 3
        left_arm_y = arm_root_y + 5 + breath_offset
        right_arm_x = fx + 3
        right_arm_y = arm_root_y + 5 + breath_offset
        draw_line(
            buffer, fx, arm_root_y + breath_offset, left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset, right_arm_x, right_arm_y, faction_color, line_width
        )
    elif state == "dying":
        # 倒下: 手臂平放
        left_arm_x = fx - 4 * dir_sign
        left_arm_y = arm_root_y + breath_offset + body_shift_y + 3
        right_arm_x = fx - 1 * dir_sign
        right_arm_y = arm_root_y + breath_offset + body_shift_y + 2
        draw_line(
            buffer, fx, arm_root_y + breath_offset + body_shift_y,
            left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset + body_shift_y,
            right_arm_x, right_arm_y, faction_color, line_width
        )
    elif state == "arguing":
        # 争吵: 手臂向前伸出（指对方）
        left_arm_x = fx - 2 * dir_sign
        left_arm_y = arm_root_y + 2 + breath_offset + body_shift_y
        right_arm_x = fx + 6 * dir_sign
        right_arm_y = arm_root_y + breath_offset + body_shift_y
        draw_line(
            buffer, fx, arm_root_y + breath_offset + body_shift_y,
            left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset + body_shift_y,
            right_arm_x, right_arm_y, faction_color, line_width
        )
    else:
        left_arm_x = fx - 4 + (-walk_swing if state == "walking" else 0)
        right_arm_x = fx + 4 + (walk_swing if state == "walking" else 0)
        left_arm_y = arm_root_y + 4 + breath_offset
        right_arm_y = arm_root_y + 4 + breath_offset

        if state == "mining":
            right_arm_y = arm_root_y + 6
            right_arm_x = fx + 2

        if state == "attacking" or state == "fighting":
            right_arm_x = fx + 4 + attack_offset * dir_sign
            right_arm_y = arm_root_y + 2

        if state == "fleeing":
            left_arm_x = fx - 4.5 * dir_sign
            left_arm_y = arm_root_y + 2 + breath_offset
            right_arm_x = fx + 4.5 * -dir_sign
            right_arm_y = arm_root_y + 2 + breath_offset

        draw_line(
            buffer, fx, arm_root_y + breath_offset, left_arm_x, left_arm_y, faction_color, line_width
        )
        draw_line(
            buffer, fx, arm_root_y + breath_offset, right_arm_x, right_arm_y, faction_color, line_width
        )

    # 头
    head_shift_y = 0.0
    if state == "fighting":
        head_shift_y = fight_stance
    elif state == "dying":
        head_shift_y = dying_fall
    draw_circle(buffer, fx, head_y + breath_offset + head_shift_y, head_radius, secondary_color)

    # 争吵气泡 (红色感叹号)
    if state == "arguing":
        bubble_y = head_y + breath_offset + head_shift_y - 5
        # 感叹号: 竖线 + 下圆点
        draw_line(buffer, fx, bubble_y - 2, fx, bubble_y + 1, (255, 60, 60, 255), 1)
        draw_circle(buffer, fx, bubble_y + 2.5, 0.5, (255, 60, 60, 255), 0)

    # 武器绘制（附加在右臂末端）
    if weapon_visual is not None:
        weapon_type, weapon_length = weapon_visual
        wp_x = right_arm_x
        wp_y = right_arm_y
        wp_ext_x = wp_x + weapon_length * dir_sign

        if weapon_type == "spear":
            draw_line(buffer, wp_x, wp_y, wp_ext_x, wp_y - 1, faction_color, line_width)
            # 尖端小三角
            draw_line(
                buffer, wp_ext_x, wp_y - 1, wp_ext_x + 1.5 * dir_sign, wp_y - 1, faction_color, 1
            )
        elif weapon_type == "sword":
            draw_line(buffer, wp_x, wp_y, wp_ext_x, wp_y, faction_color, line_width)
            # 护手横线
            guard_x = wp_x + weapon_length * 0.3 * dir_sign
            draw_line(
                buffer, guard_x, wp_y - 1.5, guard_x, wp_y + 1.5, faction_color, 1
            )
        elif weapon_type == "shield":
            draw_circle(
                buffer,
                fx - 6 * dir_sign,
                arm_root_y + 3 + breath_offset,
                2.5,
                faction_color,
                1,
            )
        elif weapon_type == "fist":
            pass  # 徒手无附加


def draw_health_bar(
    buffer: np.ndarray,
    x: float,
    y: float,
    width: int,
    height: int,
    current_hp: float,
    max_hp: float,
    bar_color: tuple[int, int, int, int],
    bg_color: tuple[int, int, int, int],
) -> None:
    """绘制血条."""
    draw_rect(buffer, x, y, width, height, bg_color, 1)
    ratio = max(0.0, min(1.0, current_hp / max_hp))
    fill_w = int(width * ratio)
    if fill_w > 0:
        draw_rect(buffer, x, y, fill_w, height, bar_color)


def draw_building(
    buffer: np.ndarray,
    x: float,
    y: float,
    width: int,
    height: int,
    color: tuple[int, int, int, int],
    building_type: str,
    level: int = 1,
    line_width: int = 2,
) -> None:
    """绘制建筑（线条风格）.

    建筑类型:
    - workbench: 水平桌面线条 + 两条桌腿
    - barracks: 帐篷形状（三角形屋顶 + 矩形墙体）
    - resource_node: 菱形 + 发光
    """
    if building_type == "workbench":
        # 桌面 + 两条腿
        table_top_y = y
        leg_bottom_y = y + height
        draw_line(buffer, x, table_top_y, x + width, table_top_y, color, line_width)
        draw_line(buffer, x + 4, table_top_y, x + 4, leg_bottom_y, color, line_width)
        draw_line(buffer, x + width - 4, table_top_y, x + width - 4, leg_bottom_y, color, line_width)
        if level >= 2:
            # Lv2+: 上方悬挂工具标志
            tool_y = table_top_y - 10
            draw_circle(buffer, x + width // 2, tool_y, 3, color, 1)
        if level >= 3:
            # Lv3+: 发光效果
            glow_color = (color[0], color[1], color[2], 80)
            draw_circle(buffer, x + width // 2, table_top_y - 5, 8, glow_color, 1)

    elif building_type == "barracks":
        # 三角屋顶 + 矩形墙体
        roof_top_y = y
        roof_bottom_y = y + height // 3
        wall_bottom_y = y + height
        mid_x = x + width // 2
        # 屋顶三角
        draw_line(buffer, mid_x, roof_top_y, x, roof_bottom_y, color, line_width)
        draw_line(buffer, mid_x, roof_top_y, x + width, roof_bottom_y, color, line_width)
        draw_line(buffer, x, roof_bottom_y, x + width, roof_bottom_y, color, line_width)
        # 墙体矩形
        draw_rect(buffer, x + 2, roof_bottom_y, width - 4, wall_bottom_y - roof_bottom_y, color, 1)
        # 门
        door_x = x + width // 2 - 3
        draw_rect(
            buffer, door_x, wall_bottom_y - 8, 6, 8, (color[0], color[1], color[2], 120), 1
        )

    elif building_type == "resource":
        # 菱形
        cx = x + width / 2
        cy = y + height / 2
        half_w = width / 2
        half_h = height / 2
        draw_line(buffer, cx, y, x + width, cy, color, line_width)
        draw_line(buffer, x + width, cy, cx, y + height, color, line_width)
        draw_line(buffer, cx, y + height, x, cy, color, line_width)
        draw_line(buffer, x, cy, cx, y, color, line_width)


def draw_resource_glow(
    buffer: np.ndarray,
    x: float,
    y: float,
    size: int,
    color: tuple[int, int, int, int],
    glow_phase: float,
) -> None:
    """在资源点上绘制发光效果."""
    cx = x + size / 2
    cy = y + size / 2
    # 发光圆圈
    glow_radius = int(size * 0.6 + glow_phase * 3)
    glow_alpha = min(80, int(abs(math.sin(glow_phase * 0.1)) * 80))
    glow_color = (color[0], color[1], color[2], glow_alpha)
    draw_circle(buffer, cx, cy, glow_radius, glow_color, 1)



