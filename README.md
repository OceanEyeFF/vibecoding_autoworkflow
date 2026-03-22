---
title: "AutoWorkflow"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# AutoWorkflow

> 当前主线已经收口为 `product / docs / toolchain + hidden mounts`。业务源码、文档真相、辅助工具各自独立，本地 `.claude/` 与 `.agents/` 只保留部署结果。

## 当前入口

- 文档模块入口：`docs/README.md`
- Agent 规则入口：`AGENTS.md`
- 根目录分层：`docs/knowledge/foundations/root-directory-layering.md`
- Toolchain 分层：`docs/knowledge/foundations/toolchain-layering.md`
- Memory Side 边界：`docs/knowledge/memory-side/layer-boundary.md`
- Memory Side 总览：`docs/knowledge/memory-side/overview.md`
- Skill / Agent 模型：`docs/knowledge/memory-side/skill-agent-model.md`

## 当前仓库状态

- `product/memory-side/skills/`：canonical skill 源码
- `product/memory-side/adapters/agents/`：Codex / OpenAI adapter 源码
- `product/memory-side/adapters/claude/`：Claude adapter 源码
- `docs/knowledge/`：canonical truth 与基础治理
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

## 使用建议

1. 先读 `docs/README.md`，先分清文档层内部结构。
2. 再读 `docs/knowledge/foundations/root-directory-layering.md`，先分清根目录层级。
3. 再读 `docs/knowledge/memory-side/layer-boundary.md`，先分清 `Memory Side` 的通用层和实例层。
4. 需要理解能力语义时，读 `docs/knowledge/memory-side/overview.md` 和 `docs/knowledge/memory-side/skill-agent-model.md`。
5. 需要改业务代码时，优先进入 `product/`。
6. 需要本地挂载或全局安装时，使用 `toolchain/scripts/deploy/adapter_deploy.py`。

## 说明

- `docs/knowledge/` 已经不再承载 guide、analysis 和 reference 的全部职责。
- `.agents/` 与 `.claude/` 已经不再作为源码层。
- `GUIDE.md` 和 `ROADMAP.md` 继续保留为兼容入口。
