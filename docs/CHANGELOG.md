# Desktop Battle - 变更日志

## 格式

```
## [日期] - 变更类型
### 变更内容
- 具体变更描述
```

---

## [2026-07-15] - 初始化

### 文档创建
- 创建 `PROJECT_OVERVIEW.md` — 项目总览、核心玩法、文档驱动流程
- 创建 `TECHNICAL_SPEC.md` — 技术栈、系统架构、渲染管线、物理引擎
- 创建 `UNIT_DESIGN.md` — 单位属性、阵营区分、外观绘制、生命周期
- 创建 `WEAPON_DESIGN.md` — 武器列表、制作链、伤害平衡、资源类型
- 创建 `BUILDING_DESIGN.md` — 建筑列表、建造流程、经济系统
- 创建 `BEHAVIOR_DESIGN.md` — 行为树架构、阵营策略、行为定义
- 创建 `PHYSICS_DESIGN.md` — 物理引擎、碰撞系统、地形、攀爬
- 创建 `LOGGING_DESIGN.md` — 日志系统、行为日志、系统日志、错误日志
- 创建 `CHANGELOG.md` — 变更日志
- 创建 `PLAN.md` — 阶段开发计划

### 项目初始化
- 创建项目目录结构 `src/`
- 创建 `requirements.txt`
- 创建 `.gitignore`

---

## [2026-07-15] - 需求补充：托盘图标 + 信息面板

### 文档更新
- 更新 `PROJECT_OVERVIEW.md` — V1范围增加托盘图标、右键菜单、信息面板、设置对话框
- 更新 `TECHNICAL_SPEC.md` — 新增 `infi.systray` 依赖、UI Layer 架构图、`src/ui/` 模块（tray/panel/settings）、系统托盘详细设计、信息面板布局与交互、设置对话框规格
- 更新 `PLAN.md` — Phase 1 增加托盘图标，Phase 11 增加面板和设置

---

## [2026-07-15] - 需求补充：外部AI接入

### 文档更新
- 更新 `TECHNICAL_SPEC.md` — 新增 `httpx` 依赖、`src/ai/` 模块（client/strategy/prompts/strategy_log）、外部AI接入详细设计（架构/配置/提示词/执行流程/降级/策略日志）
- 更新 `PLAN.md` — 新增 Phase 12 外部AI接入，原 Phase 12 整合调优顺延为 Phase 13
