---
title: "CHANGELOG - 规划体系变更记录"
status: active
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# CHANGELOG - 规划体系变更记录

> 只记录已经落地的规划文档和结构调整。
> 历史条目保留当时的命名习惯；当前主线以最新入口文档为准。

## [Unreleased]

- 暂无未归档条目

## [2026-03-17] 规划体系收口

### Added

- 新增 `docs/planning/WORKBOARD.md` 作为统一任务台账
- 新增根目录 `GUIDE.md` / `ROADMAP.md` 兼容入口

### Changed

- 重写 `docs/overview/guide.md`，清除失效 SoT 和旧主线路径
- 重写 `docs/overview/roadmap.md`，把路线图降回“优先级 + 退出条件”
- 重写 `docs/planning/README.md`，明确 `WORKBOARD / SPRINT / CHANGELOG` 的职责
- 重写 `docs/planning/SPRINT.md`，只保留当前迭代承诺
- `docs/planning/BACKLOG.md` 退役为兼容跳转页

## [2026-03-11] 任务管理区建立

### Added

- 建立 `docs/planning/` 目录，作为规划与任务文档入口
- 建立 `docs/ideas/` 目录，作为研究与想法入口

### Changed

- 文档主目录重构为 `overview / modules / interfaces / knowledge`
