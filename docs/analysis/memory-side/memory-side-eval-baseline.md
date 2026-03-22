---
title: "Memory Side Repo-local Adapter 评测基线"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# Memory Side Repo-local Adapter 评测基线

> 目的：为本仓库 `Codex` 与 `Claude` 的 `Memory Side` adapter 提供一套最小、稳定、可人工复核的评测基线，防止适配层反过来污染真相层。本页属于仓库实现层，不是跨仓库通用验收标准。

先建立通用边界，再读本页：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)

## 一、评测对象

当前评测的是两类对象：

- `product/memory-side/adapters/` 下的 adapter 源码
- `.agents/skills/` 与 `.claude/skills/` 下的 repo-local deploy target

不在本轮评测范围内的内容：

- 大 catalog 式 Agent 编排
- 复杂 subagents
- Flow Side 运行时

## 二、必须保持成立的不变量

下面这些条件必须一直成立：

1. 项目真相仍然在 `docs/knowledge/`
2. canonical skill 源码仍然在 `product/memory-side/skills/`
3. `.agents/` 与 `.claude/` 只属于 deploy target，不是源码层
4. 当前只维护 3 个 `Memory Side` skills
5. backend 差异只影响适配方式，不改变主线规则和输出契约

## 三、核心评测维度

| 维度 | 要看的问题 | 通过标准 |
|---|---|---|
| Truth Preservation | adapter 有没有开始持有项目真相 | adapter 只回指 canonical docs / canonical skill source |
| Source Discipline | 业务源码有没有被改回 deploy target | 真实实现仍然只在 `product/` |
| Output Stability | 输出格式有没有漂移 | 仍符合 canonical output format |
| Backend Parity | Codex / Claude 有没有出现能力边界偏移 | 两边都只做同一组能力，不私加规则 |
| Minimality | 这轮是否被扩成 catalog 或复杂编排 | 仍是最小可用 backend adapter |

## 四、最小人工检查清单

每次落地或调整 adapter 后，至少检查下面几项：

- wrapper 是否先读 canonical skill，再读 canonical docs
- wrapper 是否只保存 backend adapter 说明，而没有复制规则正文
- `knowledge-base-skill` 是否仍只处理文档体系接管和入口修正
- `context-routing-skill` 是否仍只生成最小 `Route Card`
- `writeback-cleanup-skill` 是否仍只生成最小 `Writeback Card`
- Codex 侧 `openai.yaml` 是否只保留 interface metadata
- repo-local `.agents/` 与 `.claude/` 是否确实由部署脚本生成

## 五、失败信号

如果出现下面任一现象，应视为适配偏航：

- adapter 内开始出现大段 `Memory Side` 规则正文副本
- 业务源码开始直接写回 `.agents/` 或 `.claude/`
- `.agents/` 或 `.claude/` 被当成 source of truth
- `Route Card` 变成多步执行计划
- `Writeback Card` 变成长复盘
- Codex 和 Claude 出现不同的真相入口或不同的分层规则

## 六、相关文档

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
- [Memory Side Repo-local Auto Research Loop](./memory-side-auto-research-loop.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](../../operations/memory-side/codex-deployment-help.md)
- [Claude Memory Side Repo-local Adapter 适配帮助](../../operations/memory-side/claude-adaptation-help.md)
