---
title: "Task Interface Repo-local Adapter 评测基线"
status: active
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Task Interface Repo-local Adapter 评测基线

> 目的：为本仓库 `Codex` 与 `Claude` 的 `Task Interface` adapter 提供一套最小、稳定、可人工复核的评测基线，防止适配层反过来污染 `Task Contract` 真相层。本页属于仓库实现层，不是跨仓库通用验收标准。

先建立通用边界，再读本页：

- [项目 Partition 模型](../../knowledge/foundations/partition-model.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)

## 一、评测对象

当前评测的是两类对象：

- `product/task-interface/adapters/` 下的 adapter 源码
- `.agents/skills/` 与 `.claude/skills/` 下的 repo-local deploy target

不在本轮评测范围内的内容：

- 大 catalog 式 Agent 编排
- 复杂 subagents
- 宿主调用层或执行编排
- 尚未存在的 `toolchain/evals/task-interface/` benchmark 资产

## 二、必须保持成立的不变量

下面这些条件必须一直成立：

1. `Task Contract` 真相仍然在 `docs/knowledge/`
2. canonical skill 源码仍然在 `product/task-interface/skills/`
3. `.agents/` 与 `.claude/` 只属于 deploy target，不是源码层
4. 当前 `Task Interface` 只维护 `task-contract-skill`
5. backend 差异只影响适配方式，不改变 `Task Contract` 结构和边界

## 三、核心评测维度

| 维度 | 要看的问题 | 通过标准 |
|---|---|---|
| Truth Preservation | adapter 有没有开始持有 `Task Contract` 真相 | adapter 只回指 canonical docs / canonical skill source |
| Source Discipline | 业务源码有没有被改回 deploy target | 真实实现仍然只在 `product/` |
| Output Stability | `Task Contract` 结构有没有漂移 | 仍符合 canonical template 中定义的固定结构 |
| Backend Parity | Codex / Claude 有没有出现能力边界偏移 | 两边都只做同一组能力，不私加规则 |
| Minimality | 这轮是否被扩成 catalog 或复杂编排 | 仍是最小可用 backend adapter |

## 四、最小人工检查清单

每次落地或调整 adapter 后，至少检查下面几项：

- wrapper 是否先读 canonical skill，再读 canonical docs
- wrapper 是否只保存 backend adapter 说明，而没有复制规则正文
- `task-contract-skill` 是否仍只产出固定结构的 `Task Contract`
- `pending` 项是否被明确保留，而不是用猜测补齐
- Codex 侧 `openai.yaml` 是否只保留 interface metadata
- repo-local `.agents/` 与 `.claude/` 是否确实由部署脚本生成

## 五、当前阶段的验证面

当前仓库还没有独立的 `toolchain/evals/task-interface/` 测量面。

因此，本阶段的最小验证面是：

- `product/task-interface/skills/task-contract-skill/`
- `product/task-interface/adapters/agents/skills/task-contract-skill/`
- `product/task-interface/adapters/claude/skills/task-contract-skill/`
- `toolchain/scripts/deploy/adapter_deploy.py` 的 local / global dry run
- 人工核对输出结构是否与 `task-contract-template.md` 一致

## 六、失败信号

如果出现下面任一现象，应视为适配偏航：

- adapter 内开始出现大段 `Task Contract` 规则正文副本
- 业务源码开始直接写回 `.agents/` 或 `.claude/`
- `.agents/` 或 `.claude/` 被当成 source of truth
- `Task Contract` 退化成多步执行计划
- `Task Contract` 开始混入 `Route Card` 或 `Writeback Card` 字段
- Codex 和 Claude 出现不同的真相入口或不同的字段边界

## 七、后续扩展落点

如果后续需要程序化评测，新增资产应落到：

```text
toolchain/evals/task-interface/
```

优先补的对象应是：

- `Task Contract` 输出 schema
- 最小评测场景集
- 对 `confirmed / pending` 边界的 rubric

推进顺序上，先补最小测量面，再考虑共享 runner 或额外 backend：

- [Repo-local Eval 研究推进步骤](../eval-method-evolution.md)

在这些资产落地前，本页仍以人工可复核基线为准。

## 八、相关文档

- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Task Contract Skill 骨架](../../knowledge/task-interface/skills/task-contract-skill.md)
- [Repo-local Eval 研究推进步骤](../eval-method-evolution.md)
- [Codex Task Interface Repo-local Adapter 部署帮助](../../operations/task-interface/codex-deployment-help.md)
- [Claude Task Interface Repo-local Adapter 适配帮助](../../operations/task-interface/claude-adaptation-help.md)
