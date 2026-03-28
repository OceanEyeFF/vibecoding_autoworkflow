# Analysis

`docs/analysis/` 只保留已准入的研究说明，不作为当前项目真相的默认执行入口。

当前状态：

- 当前已有 research/eval 边界文档：
  - [research-eval-contracts.md](./research-eval-contracts.md)
  - [research-eval-observability.md](./research-eval-observability.md)
- 当前已有 autoresearch 分阶段研究合同：
  - [autoresearch-p0-1-contract-and-data-plane.md](./autoresearch-p0-1-contract-and-data-plane.md)
  - [autoresearch-p0-2-worktree-control-shell.md](./autoresearch-p0-2-worktree-control-shell.md)
  - [autoresearch-p0-3-baseline-loop-and-round-execution.md](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
  - [autoresearch-p1-1-mutation-registry.md](./autoresearch-p1-1-mutation-registry.md)
  - [autoresearch-p1-2-worker-contract-and-minimal-selector.md](./autoresearch-p1-2-worker-contract-and-minimal-selector.md)
  - [autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md](./autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md)
  - [autoresearch-p1-final-code-audit-and-followups.md](./autoresearch-p1-final-code-audit-and-followups.md) — 合并后的 P1.Final 代码复核、当前状态与后续动作
  - [autoresearch-p1-final-followup-task-plan.md](./autoresearch-p1-final-followup-task-plan.md) — 按任务边界、依赖和难度拆解的后续实现规划
  - [autoresearch-p2-lightweight-single-prompt-codex-loop.md](./autoresearch-p2-lightweight-single-prompt-codex-loop.md) — 单 Prompt、`codex -> codex` 的轻量迭代设计草案
  - [autoresearch-p2-lightweight-single-prompt-codex-task-plan.md](./autoresearch-p2-lightweight-single-prompt-codex-task-plan.md) — 面向多 Agent 执行的 P2 任务规划文档
  - [autoresearch-p2-batch3-prereq-task-plan.md](./autoresearch-p2-batch3-prereq-task-plan.md) — Batch 3 正式开始前的 3 个前序任务规划，用于先隔离 smoke 夹具并固定 stop/replay 测试语义

说明：

- `research-eval-*` 固定的是当前 research runner 与 eval contract 的边界
- `autoresearch-p0-*` 固定的是 `autoresearch` 轨道在 P0 阶段的局部合同，不自动覆盖 `docs/knowledge/`、`docs/operations/` 或实现入口
- `autoresearch-p1-*` 固定的是 `mutation registry -> worker contract -> selector -> feedback distillation` 的阶段边界；已落地实现仍应继续回写到 `toolchain/` 入口说明
- `autoresearch-p2-*` 固定的是在当前轨道上进一步收窄为“单 Prompt、Codex-only、低侵入”方案的设计边界；截至 `2026-03-28`，已落地的运行说明与已验证边界已承接到 `docs/operations/autoresearch-minimal-loop.md` 与 `toolchain/scripts/research/README.md`

## 准入与升格规则

- `analysis/` 允许固定研究轨道的阶段边界、评测口径和实验控制模型
- `analysis/` 不允许单独充当当前仓库主线规则的最终落点
- 如果某条研究结论被接受，必须同步写入承接层：
  - 稳定规则和边界进 `docs/knowledge/`
  - repo-local runbook 进 `docs/operations/`
  - 已实现 contract 进 `toolchain/`、`product/` 及其入口文档
- 原始 `analysis/` 文档继续保留为研究记录，并回链到已承接的主线文档

AI 先读什么：

1. `docs/knowledge/README.md`
2. `docs/knowledge/foundations/README.md`
3. `docs/knowledge/foundations/docs-governance.md`
4. `docs/knowledge/foundations/toolchain-layering.md`
5. 只有任务明确要求历史研究或新准入研究时，再进入这里

暂时不要先读什么：

- `docs/reference/`
- `docs/archive/`
- 业务源码目录，除非当前任务需要交叉核对实现

这里适合放：

- 已准入的研究说明
- 某条研究轨道的阶段性合同
- 稳定的复盘结论

这里不适合放：

- 当前主线规则
- 业务源码真相
- 运行期临时结果
- 未准入的重型评测设计
