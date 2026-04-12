---
title: "AutoWorkflow"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# AutoWorkflow

> 本项目是一个 AI coding 的 repo-side contract layer。它不负责完整执行编排，只负责统一 AI 进入仓库时的阅读入口、上下文边界、静态真相层，以及任务结束后的回写与清理。

## 仓库定位

- 主线只认三块正式内容区：`product/`、`docs/`、`toolchain/`。
- `product/` 放 canonical skills 与 adapters 源码，`docs/` 放真相与治理，`toolchain/` 放部署、检查和评测工具。
- `.agents/`、`.claude/`、`.opencode/` 是 repo-local mount / deploy target；`.autoworkflow/`、`.spec-workflow/`、`.serena/` 是 repo-local state；`.nav/` 只是 compatibility navigation。

## 根级入口角色

| 文件 | 职责 |
|------|------|
| [`README.md`](./README.md) | 根级 landing page，先回答“这是什么仓库、主线在哪” |
| [`INDEX.md`](./INDEX.md) | quick index，按任务目标把人或 agent 导向正确入口 |
| [`GUIDE.md`](./GUIDE.md) / [`ROADMAP.md`](./ROADMAP.md) | 兼容入口，不单独定义主线 |
| [`AGENTS.md`](./AGENTS.md) | agent-facing 最小工作规则入口；若冲突，以 `docs/project-maintenance/`、`docs/deployable-skills/` 与 `docs/autoresearch/` 为准 |

## 默认阅读路径

1. [`docs/README.md`](./docs/README.md)
2. [`docs/project-maintenance/README.md`](./docs/project-maintenance/README.md)
3. [`docs/project-maintenance/foundations/README.md`](./docs/project-maintenance/foundations/README.md)
4. [`docs/project-maintenance/foundations/root-directory-layering.md`](./docs/project-maintenance/foundations/root-directory-layering.md)
5. [`AGENTS.md`](./AGENTS.md)
6. 按任务进入 [`docs/deployable-skills/memory-side/README.md`](./docs/deployable-skills/memory-side/README.md)、[`docs/deployable-skills/task-interface/README.md`](./docs/deployable-skills/task-interface/README.md)、[`product/README.md`](./product/README.md) 或 [`toolchain/README.md`](./toolchain/README.md)

## 继续往哪走

- 想按任务快速找入口：看 [`INDEX.md`](./INDEX.md)
- 想理解文档真相层：看 [`docs/README.md`](./docs/README.md)
- 想理解业务源码入口：看 [`product/README.md`](./product/README.md)
- 想理解工具层与检查入口：看 [`toolchain/README.md`](./toolchain/README.md)

## 许可证

- 当前仓库采用 MIT License。
- 正式授权文本以根目录 [`LICENSE`](./LICENSE) 文件为准。
- 当前仓库的授权边界只看正式许可证文件，不依赖 README 文案。

## 当前提醒

- 不要把 `.agents/`、`.claude/`、`.opencode/` 当成源码层或真相层。
- 不要把 `.autoworkflow/`、`.spec-workflow/`、`.serena/` 当成默认阅读主线。
- 不要把 `.nav/` 当成结构定义层。
