# Analysis

`docs/analysis/` 只保留已准入的研究说明与受控执行规划，不作为当前项目真相的默认执行入口。

## 当前入口规则

- 默认只把“当前研究文档”和“当前仍在驱动实现的执行规划”暴露为入口。
- 能承担默认入口的只能是“目录页型文件”；具体层级口径见 [../operations/autoresearch-closeout-entry-layering.md](../operations/autoresearch-closeout-entry-layering.md)。
- 当前 `docs/analysis/README.md` 负责 `analysis/` 层分流；本目录中的 goals、task list 和其他正文页都属于叶子页，不单独承担默认入口。
- 已完成、已替换或只保留 lineage 的 task-plan 文档，必须改成 `status: superseded`，并移出默认当前状态清单。
- 历史 planning 必须在页首明确“本文不是当前默认入口”，并前跳回目录页或仍 active 的正文。
- 研究结论一旦被主线接受，仍必须承接到 `docs/knowledge/`、`docs/operations/`、`toolchain/` 或 `product/`。

## 文档盘点

| Bucket | Status | Count | 用途 |
| --- | --- | ---: | --- |
| Research / Eval 边界 | `active` | 2 | 固定 research runner、eval 与 observability 合同 |
| Autoresearch 阶段合同与设计边界 | `active` | 8 | 固定 phase contract、代码复核与当前设计基线 |
| 当前执行规划 | `active` | 3 | 当前仍用于直接驱动实现或收口治理的受控任务入口 |
| 历史执行规划 | `superseded` | 5 | 保留 lineage，不作为默认执行入口 |

## 当前研究文档

- Research / Eval 边界：
  - [research-eval-contracts.md](./research-eval-contracts.md)
  - [research-eval-observability.md](./research-eval-observability.md)
- Autoresearch 阶段合同与设计边界：
  - [autoresearch-p0-1-contract-and-data-plane.md](./autoresearch-p0-1-contract-and-data-plane.md)
  - [autoresearch-p0-2-worktree-control-shell.md](./autoresearch-p0-2-worktree-control-shell.md)
  - [autoresearch-p0-3-baseline-loop-and-round-execution.md](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
  - [autoresearch-p1-1-mutation-registry.md](./autoresearch-p1-1-mutation-registry.md)
  - [autoresearch-p1-2-worker-contract-and-minimal-selector.md](./autoresearch-p1-2-worker-contract-and-minimal-selector.md)
  - [autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md](./autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md)
  - [autoresearch-p1-final-code-audit-and-followups.md](./autoresearch-p1-final-code-audit-and-followups.md)
  - [autoresearch-p2-lightweight-single-prompt-codex-loop.md](./autoresearch-p2-lightweight-single-prompt-codex-loop.md)

## 当前执行规划

说明：

- 本节仍是 `analysis/` 层目录页分流，不把下面的正文页提升成并列默认入口。

- [autoresearch-p2-tmp-exrepo-runtime-task-plan.md](./autoresearch-p2-tmp-exrepo-runtime-task-plan.md)  
  当前用于驱动 `tmp exrepo + materialized suite + maintenance script` 两阶段施工。
- [autoresearch-closeout-governance-goals.md](./autoresearch-closeout-governance-goals.md)  
  当前 closeout 的目标正文叶子页；默认分流入口仍以本页为准。
- [autoresearch-closeout-governance-task-list.md](./autoresearch-closeout-governance-task-list.md)  
  当前 closeout 的任务正文叶子页；默认分流入口仍以本页为准。

## 历史执行规划

说明：

- 下列文档都只保留为 lineage 叶子页，不作为默认入口。

- [autoresearch-p2-stage-closeout-and-next-stage-platform-plan.md](./autoresearch-p2-stage-closeout-and-next-stage-platform-plan.md)  
  已被更明确的收口治理目标文档与治理任务清单取代，保留为上一版宽口径平台期规划 lineage。
- [autoresearch-p1-final-followup-task-plan.md](./autoresearch-p1-final-followup-task-plan.md)  
  保留为 P1 follow-up lineage，不再作为当前执行入口。
- [autoresearch-p2-exrepo-input-hygiene-task-plan.md](./autoresearch-p2-exrepo-input-hygiene-task-plan.md)  
  已被更收敛的 TMP exrepo 运行时迁移规划取代，保留为上一版 exrepo 输入面修复记录。
- [autoresearch-p2-lightweight-single-prompt-codex-task-plan.md](./autoresearch-p2-lightweight-single-prompt-codex-task-plan.md)  
  已被更收窄的 P2 施工计划取代，保留为原始任务拆解记录。
- [autoresearch-p2-batch3-prereq-task-plan.md](./autoresearch-p2-batch3-prereq-task-plan.md)  
  已完成其前序隔离任务，保留为 Batch 3 开工前的历史规划。

## 准入与升格规则

- `analysis/` 允许固定研究轨道的阶段边界、评测口径和实验控制模型。
- `analysis/` 不允许单独充当当前仓库主线规则的最终落点。
- 如果某条研究结论被接受，必须同步写入承接层：
  - 稳定规则和边界进 `docs/knowledge/`
  - repo-local runbook 进 `docs/operations/`
  - 已实现 contract 进 `toolchain/`、`product/` 及其入口文档
- 原始 `analysis/` 文档继续保留为研究记录，并回链到已承接的主线文档。

## AI 先读什么

1. `docs/knowledge/README.md`
2. `docs/knowledge/foundations/README.md`
3. `docs/knowledge/foundations/docs-governance.md`
4. `docs/knowledge/foundations/toolchain-layering.md`
5. 只有任务明确要求历史研究或新准入研究时，再进入这里

## 暂时不要先读什么

- `docs/reference/`
- `docs/archive/`
- 业务源码目录，除非当前任务需要交叉核对实现

## 这里适合放

- 已准入的研究说明
- 某条研究轨道的阶段性合同
- 当前仍需要执行的受控任务规划
- 稳定的复盘结论

## 这里不适合放

- 当前主线规则
- 业务源码真相
- 运行期临时结果
- 已失效但仍冒充当前入口的旧 task-plan
