# Analysis

`docs/analysis/` 只保留已准入的研究说明与受控执行规划，不作为当前项目真相的默认执行入口。

`analysis/` 不长期承载 `suspended` 文档；暂停或退出当前执行面的规划一律转为 `superseded`，而不是继续停在共享文档层。

## 当前入口规则

- 本页是 `analysis/` 唯一默认分流入口；正文页不单独承担默认入口。
- 默认只把“当前研究文档”暴露为入口，不再把历史 planning / audit / closeout 叶子页混进当前阅读面。
- closeout 叶子页已经退出“当前执行规划”语义，只保留 lineage / audit 价值。
- P0 / P1 / P2 phase contract 与设计边界仍保持 active，不因为本轮入口收口而降级。
- 已完成、已替换或只保留 lineage 的 task-plan 文档，必须改成 `status: superseded`，并移出默认当前状态清单。
- 历史 planning 必须在页首明确“本文不是当前默认入口”，并前跳回目录页或仍 active 的正文。
- 研究结论一旦被主线接受，仍必须承接到 `docs/knowledge/`、`docs/operations/`、`toolchain/` 或 `product/`。

## 文档盘点

| Bucket | Status | Count | 用途 |
| --- | --- | ---: | --- |
| Research / Eval 边界 | `active` | 2 | 固定 research runner 与 observability 合同 |
| Autoresearch 阶段合同与设计边界 | `active` | 8 | 固定 phase contract、唯一当前开发目标与当前设计基线 |
| 历史研究 lineage | `superseded` | 4 | 保留上一轮问题 framing、审计与产品化判断，不作为当前研究入口 |
| Closeout lineage / audit | `superseded` | 2 | 保留 closeout 目标与治理设想的 lineage，不作为默认执行入口 |
| 历史执行规划 | `superseded` | 8 | 保留 lineage，不作为默认执行入口 |

## 当前研究文档

- Research / Eval 边界：
  - [research-eval-contracts.md](./research-eval-contracts.md)
  - [research-eval-observability.md](./research-eval-observability.md)
- Autoresearch 阶段合同与设计边界：
  - [autoresearch-next-stage-cli-modularity-plan.md](./autoresearch-next-stage-cli-modularity-plan.md)  
    当前 `autoresearch` 唯一保留的开发目标入口；下一阶段默认只关注 CLI 模块化与插拔化建议。
  - [autoresearch-p0-1-contract-and-data-plane.md](./autoresearch-p0-1-contract-and-data-plane.md)
  - [autoresearch-p0-2-worktree-control-shell.md](./autoresearch-p0-2-worktree-control-shell.md)
  - [autoresearch-p0-3-baseline-loop-and-round-execution.md](./autoresearch-p0-3-baseline-loop-and-round-execution.md)
  - [autoresearch-p1-1-mutation-registry.md](./autoresearch-p1-1-mutation-registry.md)
  - [autoresearch-p1-2-worker-contract-and-minimal-selector.md](./autoresearch-p1-2-worker-contract-and-minimal-selector.md)
  - [autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md](./autoresearch-p1-3-feedback-distillation-and-adaptive-scheduler.md)
  - [autoresearch-p2-lightweight-single-prompt-codex-loop.md](./autoresearch-p2-lightweight-single-prompt-codex-loop.md)

## Closeout Lineage / Audit

说明：

- 本节只保留 `autoresearch` closeout 的 lineage / audit 叶子页。
- 它们不是当前执行规划，也不再承担默认入口。
- 如需复核 closeout 规则、cleanup 记录或 gate 证据，再按需进入 `docs/operations/` 下的 closeout 专项页。

- [autoresearch-closeout-governance-goals.md](./autoresearch-closeout-governance-goals.md)  
  2026-04 closeout 的目标基线，现只保留 lineage 和完成判断记录。
- [autoresearch-closeout-governance-task-list.md](./autoresearch-closeout-governance-task-list.md)  
  一次已收起的“收口后中期治理”设想，现只保留 superseded lineage，不驱动当前实现。

## 历史研究 Lineage

说明：

- 本节只保留已被替换的问题 framing 文档。
- 它们只用于解释“为什么当时这样评估”，不再作为当前研究入口。

- [prompt-templates-harness-operations-package-assessment.md](./prompt-templates-harness-operations-package-assessment.md)  
  保留为上一轮“repo-local execution template / 包本体 vs 实例化层”评估框架的 lineage；当前默认入口已回到目录页与现行 shim / product 入口。
- [prompt-templates-productization-and-skill-distribution-assessment.md](./prompt-templates-productization-and-skill-distribution-assessment.md)  
  保留为 `prompt-templates` 产品化判断的 lineage；当前现行落位已由 `product/harness-operations` 与 `docs/operations/prompt-templates/` 承接。
- [autoresearch-p1-final-code-audit-and-followups.md](./autoresearch-p1-final-code-audit-and-followups.md)  
  保留为 P1.Final 审计与 follow-up 判断记录；当前默认入口已回到阶段合同与运行说明。

## 历史执行规划

说明：

- 下列文档都只保留为 lineage 叶子页，不作为默认入口。

- [autoresearch-p2-stage-closeout-and-next-stage-platform-plan.md](./autoresearch-p2-stage-closeout-and-next-stage-platform-plan.md)  
  已被更明确的收口治理目标文档与治理任务清单取代，保留为上一版宽口径平台期规划 lineage。
- [prompt-templates-productization-task-plan.md](./prompt-templates-productization-task-plan.md)  
  已被当前 `product/harness-operations` 落位与 shim 治理吸收，保留为产品化改造的历史任务拆解。
- [autoresearch-p2-tmp-exrepo-runtime-task-plan.md](./autoresearch-p2-tmp-exrepo-runtime-task-plan.md)  
  `/tmp exrepo + materialized suite` 迁移与维护脚本目标已完成并归档；当前不再作为默认开发目标。
- [autoresearch-p2-repo-prompt-guidance-task-plan.md](./autoresearch-p2-repo-prompt-guidance-task-plan.md)  
  repo 级 prompt guidance 目标已从当前默认开发面收起，保留为历史任务拆解与 lineage。
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
- 已失效但仍冒充当前入口的旧 planning / audit / closeout 叶子页
