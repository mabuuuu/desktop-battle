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
    """在 RGBA buffer 上绘制关节式火柴人.

    以 (body_screen_x, body_screen_y) 为脚底锚点.
    关节系统: 肩→肘→手, 髋→膝→脚.
    idle时手臂自然垂落(肘微弯), 腿自然站立(膝微弯).
    walking时腿交替摆动(膝在摆动相弯曲更大), 手臂反向摆动.
    """
    import math as _math

    fx = body_screen_x
    fy = body_screen_y  # 脚底

    dir_sign = 1 if facing_right else -1

    # ── 骨骼尺寸 (20px高火柴人) ──
    # 身体: 脚底(fy) → 膝(fy-5) → 髋(fy-9) → 肩(fy-15) → 头(fy-18)
    hip_y = fy - 9
    shoulder_y = fy - 15
    head_y = fy - 18

    # 上臂长4px, 前臂长4px; 大腿长5px, 小腿长5px
    upper_arm_len = 4.0
    forearm_len = 4.0
    thigh_len = 5.0
    shin_len = 5.0

    # ── 动画相位 ──
    breath_offset = 0.5 if (anim_frame % 30) < 15 else 0.0

    # walking摆动
    walk_phase = 0.0
    walk_swing = 0.0
    if state == "walking":
        walk_phase = (anim_frame % 20) / 20.0
        walk_swing = _math.sin(walk_phase * _math.pi * 2) * 0.5  # 弧度

    # mining挥臂
    mining_angle = 0.0
    if state == "mining":
        mining_phase = (anim_frame % 18) / 18.0
        mining_angle = _math.sin(mining_phase * _math.pi) * 0.8

    # attacking/fighting挥臂
    attack_offset = 0.0
    if state in ("attacking", "fighting"):
        attack_phase = (anim_frame % 15) / 15.0
        if attack_phase < 0.5:
            attack_offset = attack_phase * 1.2
        else:
            attack_offset = (1.0 - attack_phase) * 1.2

    # climbing攀爬
    climb_phase = 0.0
    if state == "climbing":
        climb_phase = (anim_frame % 16) / 16.0

    # fleeing逃跑
    flee_lean = 0.0
    if state == "fleeing":
        flee_lean = 0.3  # 身体前倾弧度

    # building建造
    build_phase = 0.0
    if state == "building":
        build_phase = (anim_frame % 20) / 20.0

    # crafting制作
    craft_phase = 0.0
    if state == "crafting":
        craft_phase = (anim_frame % 24) / 24.0

    # dying倒下
    dying_progress = 0.0
    if state == "dying":
        dying_progress = min(1.0, (anim_frame % 20) / 10.0)

    # arguing争吵
    argue_phase = 0.0
    if state == "arguing":
        argue_phase = (anim_frame % 12) / 12.0

    # carrying搬运
    carry_phase = 0.0
    if state == "carrying":
        carry_phase = 1.0

    # ── 身体偏移 ──
    body_shift_y = 0.0
    body_lean = 0.0  # 身体前倾角度(弧度)
    if state == "fighting":
        body_shift_y = 1.5
    elif state == "fleeing":
        body_shift_y = 2.0
        body_lean = flee_lean
    elif state == "dying":
        body_shift_y = dying_progress * 10.0
        body_lean = dying_progress * 1.4  # 逐渐倒下
    elif state == "arguing":
        body_shift_y = 1.5

    # ── 计算关节位置 ──
    # 身体线: 髋→肩 (带前倾)
    lean_dx = _math.sin(body_lean) * 6  # 前倾水平偏移
    shoulder_x = fx + lean_dx
    shoulder_y_actual = shoulder_y + breath_offset + body_shift_y
    hip_x = fx
    hip_y_actual = hip_y + breath_offset + body_shift_y * 0.5

    # ── 腿部关节 ──
    def _leg_joints(swing_angle: float, is_front: bool) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        """计算腿的三个关节: 髋, 膝, 脚.

        swing_angle: 大腿摆动角度(正=向前, 负=向后)
        is_front: 是否是前腿(影响膝弯曲方向)
        """
        # 大腿角度(从垂直向下算, 正=向前即屏幕右方)
        thigh_angle = swing_angle
        # 大腿末端(膝)
        knee_x = hip_x + _math.sin(thigh_angle) * thigh_len
        knee_y = hip_y_actual + _math.cos(thigh_angle) * thigh_len

        # 小腿角度: 大腿角度 + 膝弯曲
        # 自然站立: 膝微弯(0.15弧度)
        # 摆动相(腿向前): 膝弯曲更大(0.6弧度)
        # 支撑相(腿向后): 膝几乎直(0.05弧度)
        if state == "walking":
            if swing_angle > 0:
                # 前摆: 膝弯曲大
                knee_bend = 0.15 + abs(swing_angle) * 1.5
            else:
                # 后蹬: 膝几乎直
                knee_bend = 0.05
        elif state == "dying":
            knee_bend = 0.3 * dying_progress
        elif state == "fighting":
            knee_bend = 0.2
        elif state == "climbing":
            knee_bend = 0.4 + _math.sin(climb_phase * _math.pi * 2) * 0.2
        else:
            # idle/mining等: 膝微弯
            knee_bend = 0.15

        shin_angle = thigh_angle + knee_bend
        foot_x = knee_x + _math.sin(shin_angle) * shin_len
        foot_y = knee_y + _math.cos(shin_angle) * shin_len

        return (hip_x, hip_y_actual), (knee_x, knee_y), (foot_x, foot_y)

    # ── 手臂关节 ──
    def _arm_joints(swing_angle: float, is_right: bool) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        """计算手臂的三个关节: 肩, 肘, 手.

        swing_angle: 上臂摆动角度(正=向前)
        is_right: 是否是右臂
        """
        # 上臂角度(从垂直向下算, 正=向前)
        upper_arm_angle = swing_angle
        # 肘位置
        elbow_x = shoulder_x + _math.sin(upper_arm_angle) * upper_arm_len
        elbow_y = shoulder_y_actual + _math.cos(upper_arm_angle) * upper_arm_len

        # 前臂角度: 上臂角度 + 肘弯曲
        # 自然垂落: 肘微弯(0.2弧度, 前臂略向前)
        # 摆动: 肘弯曲随摆动变化
        if state == "walking":
            if swing_angle > 0:
                # 前摆: 肘弯曲大
                elbow_bend = 0.3 + abs(swing_angle) * 0.8
            else:
                # 后摆: 肘较直
                elbow_bend = 0.1
        elif state == "mining" and is_right:
            # 挖矿: 右臂向下挥
            elbow_bend = 0.5 + mining_angle * 0.5
        elif state in ("attacking", "fighting") and is_right:
            # 攻击: 右臂向前伸
            elbow_bend = -0.2 + attack_offset * 0.3
        elif state == "climbing":
            elbow_bend = -0.8 + _math.sin(climb_phase * _math.pi * 2) * 0.3
        elif state == "building":
            elbow_bend = 0.6 + _math.sin(build_phase * _math.pi) * 0.3
        elif state == "crafting":
            elbow_bend = 0.4 + _math.sin(craft_phase * _math.pi * 2) * 0.3
        elif state == "carrying":
            elbow_bend = 0.3
        elif state == "dying":
            elbow_bend = 0.1 * dying_progress
        elif state == "arguing" and is_right:
            # 争吵: 右臂指向前方
            elbow_bend = -0.3 + _math.sin(argue_phase * _math.pi * 2) * 0.2
        else:
            # idle: 自然垂落, 肘微弯
            elbow_bend = 0.2

        forearm_angle = upper_arm_angle + elbow_bend
        hand_x = elbow_x + _math.sin(forearm_angle) * forearm_len
        hand_y = elbow_y + _math.cos(forearm_angle) * forearm_len

        return (shoulder_x, shoulder_y_actual), (elbow_x, elbow_y), (hand_x, hand_y)

    # ── 计算各肢体 ──
    # 腿: 左腿和右腿
    if state == "walking":
        left_leg_swing = walk_swing  # 正弦摆动
        right_leg_swing = -walk_swing  # 反相
    elif state == "climbing":
        left_leg_swing = _math.sin(climb_phase * _math.pi * 2) * 0.3
        right_leg_swing = -_math.sin(climb_phase * _math.pi * 2) * 0.3
    elif state == "dying":
        left_leg_swing = 0.0
        right_leg_swing = 0.0
    elif state == "fighting":
        left_leg_swing = -0.1
        right_leg_swing = 0.1
    elif state == "arguing":
        left_leg_swing = 0.0
        right_leg_swing = 0.0
    else:
        # idle: 微小自然摆动
        idle_sway = _math.sin(anim_frame * 0.05) * 0.03
        left_leg_swing = idle_sway
        right_leg_swing = -idle_sway

    left_hip, left_knee, left_foot = _leg_joints(left_leg_swing, False)
    right_hip, right_knee, right_foot = _leg_joints(right_leg_swing, True)

    # 手臂: 左臂和右臂
    if state == "walking":
        # 手臂与腿反向摆动
        left_arm_swing = -walk_swing * 0.7
        right_arm_swing = walk_swing * 0.7
    elif state == "mining":
        left_arm_swing = 0.1  # 左臂自然
        right_arm_swing = 0.3 + mining_angle  # 右臂挥动
    elif state in ("attacking", "fighting"):
        left_arm_swing = 0.1
        right_arm_swing = 0.5 + attack_offset
    elif state == "climbing":
        left_arm_swing = -0.8 + _math.sin(climb_phase * _math.pi * 2) * 0.3
        right_arm_swing = -0.8 - _math.sin(climb_phase * _math.pi * 2) * 0.3
    elif state == "fleeing":
        left_arm_swing = -0.4
        right_arm_swing = -0.4
    elif state == "building":
        left_arm_swing = 0.3 + _math.sin(build_phase * _math.pi) * 0.2
        right_arm_swing = 0.3 - _math.sin(build_phase * _math.pi) * 0.2
    elif state == "crafting":
        left_arm_swing = 0.2 + _math.sin(craft_phase * _math.pi * 2) * 0.15
        right_arm_swing = 0.2 - _math.sin(craft_phase * _math.pi * 2) * 0.15
    elif state == "carrying":
        left_arm_swing = 0.15
        right_arm_swing = 0.15
    elif state == "dying":
        left_arm_swing = 0.0
        right_arm_swing = 0.0
    elif state == "arguing":
        left_arm_swing = 0.1
        right_arm_swing = 0.6 + _math.sin(argue_phase * _math.pi * 2) * 0.2
    else:
        # idle: 手臂自然垂落, 微小摆动
        idle_arm_sway = _math.sin(anim_frame * 0.04) * 0.05
        left_arm_swing = idle_arm_sway
        right_arm_swing = -idle_arm_sway

    left_shoulder_pt, left_elbow, left_hand = _arm_joints(left_arm_swing, False)
    right_shoulder_pt, right_elbow, right_hand = _arm_joints(right_arm_swing, True)

    # ── 绘制 ──
    # 身体线: 髋→肩
    draw_line(buffer, hip_x, hip_y_actual, shoulder_x, shoulder_y_actual, faction_color, line_width)

    # 左腿: 髋→膝→脚
    draw_line(buffer, left_hip[0], left_hip[1], left_knee[0], left_knee[1], faction_color, line_width)
    draw_line(buffer, left_knee[0], left_knee[1], left_foot[0], left_foot[1], faction_color, line_width)

    # 右腿: 髋→膝→脚
    draw_line(buffer, right_hip[0], right_hip[1], right_knee[0], right_knee[1], faction_color, line_width)
    draw_line(buffer, right_knee[0], right_knee[1], right_foot[0], right_foot[1], faction_color, line_width)

    # 左臂: 肩→肘→手
    draw_line(buffer, left_shoulder_pt[0], left_shoulder_pt[1], left_elbow[0], left_elbow[1], faction_color, line_width)
    draw_line(buffer, left_elbow[0], left_elbow[1], left_hand[0], left_hand[1], faction_color, line_width)

    # 右臂: 肩→肘→手
    draw_line(buffer, right_shoulder_pt[0], right_shoulder_pt[1], right_elbow[0], right_elbow[1], faction_color, line_width)
    draw_line(buffer, right_elbow[0], right_elbow[1], right_hand[0], right_hand[1], faction_color, line_width)

    # 头
    head_shift_y = 0.0
    if state == "fighting":
        head_shift_y = 1.5
    elif state == "dying":
        head_shift_y = dying_progress * 10.0
    draw_circle(buffer, shoulder_x, head_y + breath_offset + head_shift_y, head_radius, secondary_color)

    # 争吵气泡 (红色感叹号)
    if state == "arguing":
        bubble_y = head_y + breath_offset + head_shift_y - 5
        draw_line(buffer, shoulder_x, bubble_y - 2, shoulder_x, bubble_y + 1, (255, 60, 60, 255), 1)
        draw_circle(buffer, shoulder_x, bubble_y + 2.5, 0.5, (255, 60, 60, 255), 0)

    # 武器绘制（附加在右手末端）
    if weapon_visual is not None:
        weapon_type, weapon_length = weapon_visual
        wp_x = right_hand[0]
        wp_y = right_hand[1]
        wp_ext_x = wp_x + weapon_length * dir_sign

        if weapon_type == "spear":
            draw_line(buffer, wp_x, wp_y, wp_ext_x, wp_y - 1, faction_color, line_width)
            draw_line(
                buffer, wp_ext_x, wp_y - 1, wp_ext_x + 1.5 * dir_sign, wp_y - 1, faction_color, 1
            )
        elif weapon_type == "sword":
            draw_line(buffer, wp_x, wp_y, wp_ext_x, wp_y, faction_color, line_width)
            guard_x = wp_x + weapon_length * 0.3 * dir_sign
            draw_line(
                buffer, guard_x, wp_y - 1.5, guard_x, wp_y + 1.5, faction_color, 1
            )
        elif weapon_type == "shield":
            draw_circle(
                buffer,
                left_hand[0],
                left_hand[1],
                2.5,
                faction_color,
                1,
            )
        elif weapon_type == "fist":
            pass


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



