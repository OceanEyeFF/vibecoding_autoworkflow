---
title: "Memory Side Adapter 评测基线"
status: active
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Memory Side Adapter 评测基线

> 目的：为 `Codex` 与 `Claude` 的 `Memory Side` backend adapter 提供一套最小、稳定、可人工复核的评测基线，防止适配层反过来污染真相层。

## 一、评测对象

当前仅评测下面两类 adapter：

- `.agents/skills/...` 下的 Codex / OpenAI repo-local wrapper
- `.claude/skills/...` 下的 Claude repo-local wrapper

不在本轮评测范围内的内容：

- 大 catalog 式 Agent 编排
- 复杂 subagents
- Flow Side 运行时

## 二、必须保持成立的不变量

下面这些条件必须一直成立：

1. 项目真相仍然在 `docs/knowledge/`
2. canonical skill 仍然在 `toolchain/skills/aw-kernel/memory-side/`
3. `Prompt` 仍然是适配规范，不是真相层
4. 当前只维护 3 个 `Memory Side` skills
5. backend 差异只影响适配方式，不改变主线规则和输出契约

只要其中任意一条失效，就应判定适配回退或重做。

## 三、核心评测维度

| 维度 | 要看的问题 | 通过标准 |
|---|---|---|
| Truth Preservation | adapter 有没有开始持有项目真相 | adapter 只回指 canonical docs / canonical skill |
| Boundary Control | skill 有没有越权扩读或扩职责 | 仍只覆盖各自 partition 的边界 |
| Output Stability | 输出格式有没有漂移 | 仍符合 canonical output format |
| Backend Parity | Codex / Claude 有没有出现能力边界偏移 | 两边都只做同一组能力，不私加规则 |
| Minimality | 这轮是否被扩成 catalog 或复杂编排 | 仍是最小可用 backend adapter |

## 四、基线场景

| ID | Skill | 输入类型 | 必须先读 | 禁止行为 | 通过标准 |
|---|---|---|---|---|---|
| KB-1 | `knowledge-base-skill` | 仓库已有文档体系，需接管 | `memory-side-baseline.md` + `knowledge-base.md` | 直接重写整个文档体系 | 输出 `Adopt` 判断、分层判断、最小入口修正 |
| KB-2 | `knowledge-base-skill` | 仓库文档体系不清，需要补入口 | canonical skill + entrypoints | 把 ideas/archive 提升为主线 | 只补主线入口、状态、索引、链接 |
| CR-1 | `context-routing-skill` | 文档类任务即将开始 | `memory-side-baseline.md` + `context-routing.md` | 把 Route Card 写成执行计划 | 输出固定字段的 `Route Card` |
| CR-2 | `context-routing-skill` | 代码类任务即将开始 | canonical routing docs + 最小代码入口 | 默认全仓扫描 | `code_entry` 精确、`do_not_read_yet` 明确 |
| WC-1 | `writeback-cleanup-skill` | 已有验证结果，需要回写 | `memory-side-baseline.md` + `writeback-cleanup.md` | 未验证内容直接进主线 | 输出固定字段的 `Writeback Card` |
| WC-2 | `writeback-cleanup-skill` | 变更不充分、证据不足 | canonical writeback docs | 用猜测填满 writeback | 明确列出 `do_not_write_back` 与 `risks_left` |
| XP-1 | 全部 | 同一任务在 Codex / Claude 上执行 | 各自 repo-local wrapper + 同一 canonical docs | 两边各写一套不同规则 | 输出边界一致，差异仅在表达和读取节奏 |

## 五、最小人工检查清单

每次落地或调整 adapter 后，至少检查下面几项：

- wrapper 是否先读 canonical skill，再读 canonical docs
- wrapper 是否只保存 backend adapter 说明，而没有复制规则正文
- `knowledge-base-skill` 是否仍只处理文档体系接管和入口修正
- `context-routing-skill` 是否仍只生成最小 `Route Card`
- `writeback-cleanup-skill` 是否仍只生成最小 `Writeback Card`
- Claude 侧是否优先项目级 skills，而不是先展开复杂 subagents
- Codex 侧 `openai.yaml` 是否只保留 interface metadata

## 六、失败信号

如果出现下面任一现象，应视为适配偏航：

- adapter 内开始出现大段 `Memory Side` 规则正文副本
- `Route Card` 变成多步执行计划
- `Writeback Card` 变成长复盘
- Codex 和 Claude 出现不同的真相入口或不同的分层规则
- Claude 侧先启动复杂 subagents，项目级 skill 反而不再是入口

## 七、建议的验收结论模板

可以用下面的最小模板记录一次评测结论：

```text
backend: Codex | Claude
skill: knowledge-base-skill | context-routing-skill | writeback-cleanup-skill
scenario: KB-1 | KB-2 | CR-1 | CR-2 | WC-1 | WC-2 | XP-1
result: pass | fail
notes:
- canonical docs loaded correctly
- output contract preserved
- no truth duplication in adapter
```

## 八、相关文档

- [Memory Side Skill 与 Agent 模型](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skill-agent-model.md)
- [Memory Side Auto Research Loop](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/analysis/memory-side-auto-research-loop.md)
- [Codex Memory Side 部署帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/codex-deployment-help.md)
- [Claude Memory Side 适配帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/claude-adaptation-help.md)
