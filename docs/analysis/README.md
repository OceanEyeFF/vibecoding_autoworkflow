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
  - [autoresearch-p1-final-risk-register-and-followups.md](./autoresearch-p1-final-risk-register-and-followups.md)
  - [autoresearch-p1-final-agent-teams-analysis.md](./autoresearch-p1-final-agent-teams-analysis.md) — Agent Teams 代码审计讨论结果（务实视角：先让循环跑起来）

说明：

- `research-eval-*` 固定的是当前 research runner 与 eval contract 的边界
- `autoresearch-p0-*` 固定的是 `autoresearch` 轨道在 P0 阶段的局部合同，不自动覆盖 `docs/knowledge/`、`docs/operations/` 或实现入口
- `autoresearch-p1-*` 固定的是 `mutation registry -> worker contract -> selector -> feedback distillation` 的阶段边界；已落地实现仍应继续回写到 `toolchain/` 入口说明

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
