# Desktop Battle - 物理设计文档

## 物理引擎

使用 `pymunk` (Chipmunk2D 的 Python 绑定) 作为物理引擎。

### 物理世界配置

```python
space = pymunk.Space()
space.gravity = (0, 900)       # 向下重力 900 px/s²
space.damping = 0.9            # 全局速度阻尼
space.collision_slop = 0.5     # 碰撞穿透容差
space.iterations = 10          # 约束求解迭代次数
```

### 坐标系转换

pymunk 使用 Y 轴向上的坐标系，屏幕使用 Y 轴向下：

```python
def physics_to_screen(pos, screen_height):
    return (pos[0], screen_height - pos[1])

def screen_to_physics(pos, screen_height):
    return (pos[0], screen_height - pos[1])
```

## 碰撞系统

### 碰撞类型

| 类型ID | 名称 | 说明 |
|--------|------|------|
| 1 | UNIT | 单位 |
| 2 | BUILDING | 建筑 |
| 3 | TERRAIN | 地形（任务栏、窗口边框） |
| 4 | RESOURCE_NODE | 资源采集点 |
| 5 | PROJECTILE | 投射物 |
| 6 | SENSOR | 感知范围（无物理碰撞） |
| 7 | DROPPED_WEAPON | 掉落武器 |

### 碰撞矩阵

|  | UNIT | BUILDING | TERRAIN | RESOURCE | PROJECTILE | SENSOR | WEAPON |
|--|------|----------|---------|----------|------------|--------|--------|
| UNIT | ✅ | ✅ | ✅ | ❌(sensor) | ✅ | ❌ | ❌(sensor) |
| BUILDING | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| TERRAIN | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| RESOURCE | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PROJECTILE | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| SENSOR | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| WEAPON | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### 碰撞回调

| 碰撞对 | 回调行为 |
|--------|---------|
| UNIT ↔ TERRAIN | 着地检测、攀爬触发 |
| UNIT ↔ UNIT | 战斗距离检测、推挤 |
| UNIT ↔ BUILDING | 建筑交互（建造、制作） |
| UNIT ↔ SENSOR(RESOURCE) | 进入采集范围 |
| UNIT ↔ SENSOR(WEAPON) | 进入拾取范围 |
| PROJECTILE ↔ UNIT | 投射物命中 |
| PROJECTILE ↔ TERRAIN | 投射物落地消失 |
| PROJECTILE ↔ BUILDING | 投射物命中建筑 |

## 地形系统

### 地面 (任务栏)

任务栏作为主要地面，单位在其上行走。

```python
# 检测任务栏位置
taskbar_rect = get_taskbar_rect()  # 通过 pywin32 获取

# 创建地面物理体
ground_body = pymunk.Body(body_type=pymunk.Body.STATIC)
ground_shape = pymunk.Segment(ground_body,
    (taskbar_rect.left, taskbar_rect.top),
    (taskbar_rect.right, taskbar_rect.top),
    2)  # 厚度2px
ground_shape.friction = 0.8
ground_shape.elasticity = 0.1
ground_shape.collision_type = COLLISION_TERRAIN
```

### 任务栏位置检测

```python
def get_taskbar_rect() -> Rect:
    """通过 Win32 API 获取任务栏位置和尺寸"""
    hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
    rect = win32gui.GetWindowRect(hwnd)
    return Rect(rect[0], rect[1], rect[2], rect[3])
```

任务栏可能在屏幕底部、顶部、左侧或右侧，需要动态检测。

### 窗口平台

桌面上的窗口作为可攀爬和站立的平台。

```python
def scan_windows() -> list[PlatformData]:
    """枚举桌面窗口，生成平台数据"""
    platforms = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            # 窗口顶部边框 → 可站立平台
            # 窗口左右边框 → 可攀爬
            platforms.append(PlatformData(
                top=(rect.left, rect.top, rect.right, rect.top),
                left=(rect.left, rect.top, rect.left, rect.bottom),
                right=(rect.right, rect.top, rect.right, rect.bottom),
                rect=rect
            ))
    win32gui.EnumWindows(callback, None)
    return platforms
```

### 窗口扫描频率

- 每2秒扫描一次桌面窗口
- 检测窗口移动/关闭/新建
- 物理体动态添加/移除

### 窗口物理体

```python
# 窗口顶部 → 站立平台
top_platform = pymunk.Segment(static_body,
    (rect.left, rect.top), (rect.right, rect.top), 2)
top_platform.friction = 0.8
top_platform.collision_type = COLLISION_TERRAIN

# 窗口左侧 → 攀爬面
left_wall = pymunk.Segment(static_body,
    (rect.left, rect.top), (rect.left, rect.bottom), 1)
left_wall.friction = 1.0  # 高摩擦力便于攀爬
left_wall.collision_type = COLLISION_TERRAIN

# 窗口右侧 → 攀爬面
right_wall = pymunk.Segment(static_body,
    (rect.right, rect.top), (rect.right, rect.bottom), 1)
right_wall.friction = 1.0
right_wall.collision_type = COLLISION_TERRAIN
```

## 单位物理

### 单位物理体

```python
body = pymunk.Body(mass=1.0, moment=pymunk.moment_for_circle(1.0, 0, 4))
body.position = (x, y)

shape = pymunk.Circle(body, 2)  # 半径2px
shape.friction = 0.6
shape.elasticity = 0.1
shape.collision_type = COLLISION_UNIT
```

### 单位移动

单位不直接设置速度，而是通过施加力实现移动：

```python
def move_toward(unit, target_x, speed=60):
    """向目标X坐标移动"""
    dx = target_x - unit.body.position.x
    direction = 1 if dx > 0 else -1
    # 施加水平力
    force = direction * speed * 10  # 力 = 速度 * 阻尼补偿
    unit.body.apply_force_at_local_point((force, 0))
    # 限制最大速度
    vx = unit.body.velocity.x
    if abs(vx) > speed:
        unit.body.velocity = (direction * speed, unit.body.velocity.y)
```

### 单位跳跃

```python
def jump(unit, impulse=300):
    """跳跃冲量"""
    if unit.on_ground:
        unit.body.apply_impulse_at_local_point((0, impulse))
```

## 攀爬物理

### 攀爬状态机

```
地面行走 → 接触窗口边框 → 进入攀爬
    ↓
攀爬中 (Kinematic模式)
    - 取消重力影响
    - 沿边框以固定速度移动
    - 可左右切换攀爬面
    ↓
到达窗口顶部 → 站上平台 (Dynamic模式)
    ↓
从平台走下/跳下 → 回到地面行走
```

### 攀爬实现

```python
def enter_climb(unit, wall_segment):
    """进入攀爬状态"""
    unit.state = "climbing"
    unit.climb_target = wall_segment
    # 切换为 Kinematic，取消重力
    unit.body.body_type = pymunk.Body.KINEMATIC
    unit.body.velocity = (0, 0)

def climb_update(unit, dt):
    """攀爬中每帧更新"""
    # 沿墙壁向上移动
    unit.body.position = (
        unit.body.position.x,
        unit.body.position.y + CLIMB_SPEED * dt
    )
    # 检测是否到达顶部
    if unit.body.position.y >= wall_top_y:
        exit_climb_to_platform(unit)

def exit_climb_to_platform(unit):
    """从攀爬切换到站在平台上"""
    unit.state = "idle"
    unit.body.body_type = pymunk.Body.DYNAMIC
    # 放置在窗口顶部
    unit.body.position = (unit.body.position.x, platform_y + 4)
    unit.body.velocity = (0, 0)
```

## 重力与下落

### 下落规则

- 单位不在任何平台/地面上时受重力影响
- 下落速度上限：500 px/s
- 下落伤害：无（火柴人不怕摔）
- 下落中可以左右移动（空中控制，简化游戏性）

### 着地检测

通过 UNIT ↔ TERRAIN 碰撞回调检测：

```python
def on_unit_land(arbiter, space, data):
    """单位着地回调"""
    unit = get_unit_from_shape(arbiter.shapes[0])
    unit.on_ground = True
    if unit.state == "falling":
        unit.state = "idle"
    return True
```

## 击退物理

攻击产生的击退通过冲量实现：

```python
def apply_knockback(target_unit, attacker_pos, knockback_force):
    """施加击退冲量"""
    dx = target_unit.body.position.x - attacker_pos.x
    direction = 1 if dx > 0 else -1
    impulse = (direction * knockback_force, knockback_force * 0.3)  # 水平+轻微上抛
    target_unit.body.apply_impulse_at_local_point(impulse)
```

## 物理步长

```python
PHYSICS_DT = 1.0 / 60.0  # 60Hz物理更新
# 每帧调用:
space.step(PHYSICS_DT)
```

物理更新在渲染之前执行，确保显示的是最新状态。
