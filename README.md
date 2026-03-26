---
title: "AutoWorkflow"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# AutoWorkflow

> 本项目是一个 AI coding 的 repo-side contract layer。它不负责完整执行编排，而是负责统一 AI 进入仓库时的阅读入口、上下文边界、静态真相层，以及任务结束后的回写与清理。

## 项目核心

- 这是一个 repo-side contract 项目，不是完整 orchestration 平台。
- 它只解决 4 件事：AI 先读什么、默认不要读什么、哪些内容属于真相层、任务结束后哪些结果可以安全回写。
- 它不把宿主工作流、复杂 agents catalog 或 subagents 编排当成项目主线。
- 当前主线已经收口为 `product / docs / toolchain + hidden mounts`：业务源码、文档真相、辅助工具各自独立，本地 `.claude/` 与 `.agents/` 只保留部署结果。

## 当前入口

- 文档模块入口：`docs/README.md`
- 知识主线入口：`docs/knowledge/README.md`
- Foundations 入口：`docs/knowledge/foundations/README.md`
- Agent 规则入口：`AGENTS.md`
- 项目 Partition 模型：`docs/knowledge/foundations/partition-model.md`
- 根目录分层：`docs/knowledge/foundations/root-directory-layering.md`
- 路径治理与 AI 告知：`docs/knowledge/foundations/path-governance-ai-routing.md`
- Docs 文档治理基线：`docs/knowledge/foundations/docs-governance.md`
- Toolchain 分层：`docs/knowledge/foundations/toolchain-layering.md`
- Task Interface / Task Contract：`docs/knowledge/task-interface/task-contract.md`
- Memory Side 边界：`docs/knowledge/memory-side/layer-boundary.md`
- Memory Side 总览：`docs/knowledge/memory-side/overview.md`
- Skill / Agent 模型：`docs/knowledge/memory-side/skill-agent-model.md`

## 当前仓库状态

- `product/memory-side/skills/`：canonical skill 源码
- `product/memory-side/adapters/agents/`：Codex / OpenAI adapter 源码
- `product/memory-side/adapters/claude/`：Claude adapter 源码
- `product/task-interface/skills/`：Task Interface canonical skill 源码
- `product/task-interface/adapters/agents/`：Task Interface 的 Codex / OpenAI adapter 源码
- `product/task-interface/adapters/claude/`：Task Interface 的 Claude adapter 源码
- `docs/knowledge/`：canonical truth 与基础治理
- `docs/knowledge/task-interface/`：Task Interface 真相与 skill skeleton
- `docs/operations/`：repo-local runbook 与部署说明
- `docs/analysis/`：评测与研究说明
- `docs/reference/`：外部参考资料
- `toolchain/scripts/` 与 `toolchain/evals/`：部署、评测与实验工具
- `.agents/skills/` 与 `.claude/skills/`：repo-local deploy target，由脚本生成

## 目录速览

| 目录 | 职责 |
|------|------|
| `product/` | 业务代码唯一源码根 |
| `docs/` | 文档真相与知识主线 |
| `toolchain/` | 脚本、评测、测试、部署工具 |
| `.agents/` | repo-local Codex / OpenAI mount |
| `.claude/` | repo-local Claude mount |
| `.autoworkflow/` `.spec-workflow/` `.serena/` | repo-local state，默认不作为读取主线 |
| `.nav/` | compatibility navigation，默认不作为执行入口 |

## 使用建议

1. 先读 `docs/README.md`，先分清文档层内部结构。
2. 再读 `docs/knowledge/README.md` 和 `docs/knowledge/foundations/README.md`，先拿到知识主线入口。
3. 再读 `docs/knowledge/foundations/root-directory-layering.md`，先分清根目录层级。
4. 再读 `docs/knowledge/foundations/path-governance-ai-routing.md` 与 `docs/knowledge/foundations/docs-governance.md`，先确认 AI 默认应进入哪一层、暂时不要进入哪一层，以及文档如何治理。
5. 再读 `docs/knowledge/memory-side/README.md` 或 `docs/knowledge/task-interface/README.md`，进入目标领域。
6. 需要改业务代码时，优先进入 `product/`。
7. 需要本地挂载或全局安装时，使用 `toolchain/scripts/deploy/adapter_deploy.py`。

## 说明

- `docs/knowledge/` 已经不再承载 guide、analysis 和 reference 的全部职责。
- `.agents/` 与 `.claude/` 已经不再作为源码层。
- `.autoworkflow/`、`.spec-workflow/`、`.serena/` 只属于运行状态层，默认不进入。
- `.nav/` 只保留兼容导航职责，不作为结构真相源。
- `GUIDE.md` 和 `ROADMAP.md` 继续保留为兼容入口。
