---
title: "AutoWorkflow"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---
# AutoWorkflow

> 一个 Codex-first 的 AI coding harness 平台，通过 repo-side contract layer 实现可控的 AI 编程工作流。

## 快速试用

确保有 Node.js 18+，在目标仓库中运行：

```bash
# 安装 Harness skills（agents backend）
npx aw-installer@next install --backend agents

# 验证安装
npx aw-installer@next verify --backend agents
```

交互式终端使用 TUI：

```bash
npx aw-installer@next tui
```

Claude Code 用户：

```bash
npx aw-installer@next install --backend claude
npx aw-installer@next verify --backend claude
```

## 选择你的启动场景

| 场景 | 文档 |
|------|------|
| 已有代码项目初始化 Harness | [init-with-code.md](docs/project-maintenance/usage-help/init-with-code.md) |
| 空项目从零开始 | [init-greenfield.md](docs/project-maintenance/usage-help/init-greenfield.md) |
| 调整目标 / 追加需求 | [goal-change-guide.md](docs/project-maintenance/usage-help/goal-change-guide.md) |

## 使用指南

- [推荐使用流程](docs/project-maintenance/usage-help/recommended-usage.md) — 从选择 backend 到 closeout 的完整路径
- [Codex / agents 后端](docs/project-maintenance/usage-help/codex.md) — agents backend 安装与使用
- [Claude Code 后端](docs/project-maintenance/usage-help/claude.md) — Claude compatibility lane

## 仓库维护者

内部结构说明、目录分层、入口分工和项目机制见 [Repository Onboarding](docs/project-maintenance/repo-onboarding.md)。

## 许可证

MIT License，以根目录 [LICENSE](./LICENSE) 文件为准。
