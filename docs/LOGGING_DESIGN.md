# Desktop Battle - 日志设计文档

## 日志系统概述

项目包含三类日志，各有独立输出通道和格式：

| 日志类型 | 用途 | 输出位置 | 保留策略 |
|---------|------|---------|---------|
| 系统日志 (System) | 引擎运行状态、资源加载、帧率 | `logs/system/` | 保留7天 |
| 行为日志 (Behavior) | 单位行为状态转换、决策 | `logs/behavior/` | 保留3天 |
| 错误日志 (Error) | 异常、崩溃、断言失败 | `logs/error/` | 永久保留 |

## 技术实现

### 日志库

使用 `loguru` 作为日志后端，统一管理三类日志。

### 日志管理器

```python
from loguru import logger
import sys
from pathlib import Path

class LogManager:
    """日志管理器，初始化三类日志通道"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 移除默认handler
        logger.remove()

        # 系统日志
        logger.add(
            self.log_dir / "system" / "{time:YYYY-MM-DD}.log",
            filter=lambda r: r["extra"].get("type") == "system",
            format="{time:HH:mm:ss.SSS} | {level:<7} | {message}",
            rotation="00:00",       # 每天轮转
            retention="7 days",
            encoding="utf-8",
        )

        # 行为日志
        logger.add(
            self.log_dir / "behavior" / "{time:YYYY-MM-DD}.log",
            filter=lambda r: r["extra"].get("type") == "behavior",
            format="{time:HH:mm:ss.SSS} | {message}",
            rotation="00:00",
            retention="3 days",
            encoding="utf-8",
        )

        # 错误日志
        logger.add(
            self.log_dir / "error" / "{time:YYYY-MM-DD}.log",
            filter=lambda r: r["extra"].get("type") == "error",
            format="{time:HH:mm:ss.SSS} | {level:<7} | {function}:{line} | {message}",
            rotation="00:00",
            retention="365 days",   # 永久保留
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
        )

        # 控制台输出 (开发模式)
        logger.add(
            sys.stderr,
            format="<level>{time:HH:mm:ss} | {level:<7} | {message}</level>",
            level="DEBUG",
        )
```

## 系统日志

### 记录内容

| 事件 | 级别 | 格式 |
|------|------|------|
| 引擎启动 | INFO | `Engine started | FPS target: {fps} | Screen: {w}x{h}` |
| 引擎关闭 | INFO | `Engine shutdown | Runtime: {duration}s` |
| 帧率统计 | DEBUG | `FPS: {fps} | Physics: {ms}ms | Render: {ms}ms | Units: {count}` |
| 窗口扫描 | INFO | `Window scan: {count} windows found | Added: {n} | Removed: {m}` |
| 任务栏检测 | INFO | `Taskbar detected: {rect} | Position: {pos}` |
| 阵营初始化 | INFO | `Faction initialized: {name} | Units: {count} | Resources: {res}` |
| 建筑建造 | INFO | `Building created: {type} | Faction: {faction} | Pos: {pos}` |
| 建筑摧毁 | INFO | `Building destroyed: {type} | Faction: {faction} | By: {attacker}` |
| 资源变化 | DEBUG | `Faction {name}: Wood {w} (+{dw}) | Ore {o} (+{do})` |
| 单位生产 | INFO | `Unit produced: {id} | Faction: {faction} | From: {building}` |
| 物理异常 | WARNING | `Physics overlap: {body_a} and {body_b} | Penetration: {depth}` |

### 帧率统计

每5秒输出一次帧率统计：

```
10:30:05.123 | DEBUG   | FPS: 58 | Physics: 2.1ms | Render: 5.3ms | Behavior: 1.2ms | Units: 12
```

## 行为日志

### 记录内容

每个单位的行为状态转换都记录到行为日志。

### 日志格式

```
{time} | [Unit:{id} {faction} {role}] {old_state} → {new_state} | {context}
```

### 行为事件

| 事件 | 格式 |
|------|------|
| 状态转换 | `[Unit:3 Red Gatherer] idle → gathering | Target: WoodNode@1 | Pos: (120, 800)` |
| 采集完成 | `[Unit:3 Red Gatherer] gathering → delivering | Carried: 20 wood | Duration: 4.0s` |
| 资源存入 | `[Unit:3 Red Gatherer] delivering → idle | Deposited: 20 wood | Faction total: 45` |
| 发现敌人 | `[Unit:7 Blue Scout] exploring → chasing | Target: Unit:3 Red | Dist: 180px` |
| 进入战斗 | `[Unit:7 Blue Scout] chasing → attacking | Target: Unit:3 Red | Weapon: spear` |
| 攻击命中 | `[Unit:7 Blue Scout] attack_hit | Target: Unit:3 Red | Damage: 4 | Target HP: 996/1000` |
| 受到攻击 | `[Unit:3 Red Gatherer] attacked_by | Attacker: Unit:7 Blue | Damage: 4 | HP: 996/1000` |
| 开始逃跑 | `[Unit:3 Red Gatherer] attacking → fleeing | HP: 180/1000 (18%)` |
| 攀爬窗口 | `[Unit:5 Red Scout] walking → climbing | Window: "Notepad" | Side: left` |
| 到达平台 | `[Unit:5 Red Scout] climbing → idle | Platform: "Notepad" top | Height: 200px` |
| 拾取武器 | `[Unit:5 Red Scout] idle → equipping | Weapon: spear | Ground pos: (300, 780)` |
| 建造开始 | `[Unit:2 Red Builder] idle → building | Target: Workbench Lv1 | Duration: 10s` |
| 建造完成 | `[Unit:2 Red Builder] building → idle | Built: Workbench Lv1 | Pos: (150, 780)` |
| 制作开始 | `[Unit:2 Red Builder] idle → crafting | Target: spear | Cost: 10 wood | Duration: 5s` |
| 制作完成 | `[Unit:2 Red Builder] crafting → idle | Crafted: spear | Placed at workbench` |
| 单位死亡 | `[Unit:3 Red Gatherer] DEAD | Killed by: Unit:7 Blue | Weapon: spear | Survived: 120s` |
| 武器掉落 | `[Weapon: spear] dropped | From: Unit:3 Red | Pos: (320, 780) | Expires: 30s` |

### 行为日志频率控制

- 状态转换：每次都记录
- 攻击命中：每3次攻击记录一次（避免日志爆炸）
- 位置更新：不记录（太频繁）
- 采集进度：不记录（在完成时记录）

## 错误日志

### 记录内容

| 事件 | 级别 | 格式 |
|------|------|------|
| 未捕获异常 | ERROR | 完整堆栈 + 上下文 |
| 物理引擎异常 | ERROR | `Physics error: {detail} | Bodies involved: {list}` |
| 渲染异常 | ERROR | `Render error: {detail} | Frame: {frame_count}` |
| 窗口API异常 | WARNING | `Win32 API error: {detail} | Function: {func}` |
| 资源不足 | WARNING | `Faction {name}: Cannot afford {item} | Need: {cost} | Have: {resources}` |
| 行为树异常 | ERROR | `Behavior tree error: {detail} | Unit: {id} | Tree: {tree}` |
| 配置错误 | CRITICAL | `Config error: {detail}` |
| 内存警告 | WARNING | `Memory usage: {mb}MB | Units: {count} | Buildings: {count}` |

### 错误日志特性

- 包含完整 Python 堆栈追踪 (`backtrace=True`)
- 包含变量值诊断 (`diagnose=True`)
- 永久保留，不自动清理
- 错误日志同时输出到系统日志

## 日志文件结构

```
logs/
├── system/
│   ├── 2026-07-15.log
│   └── 2026-07-16.log
├── behavior/
│   ├── 2026-07-15.log
│   └── 2026-07-16.log
└── error/
    ├── 2026-07-15.log
    └── 2026-07-16.log
```

## 日志性能

- 日志写入使用异步缓冲，不阻塞主线程
- 行为日志每帧最多写入10条（超出的排队到下一帧）
- 系统日志帧率统计每5秒一次
- 错误日志无限制，立即写入

## .gitignore

```
logs/
*.log
```

日志文件不纳入版本控制。
