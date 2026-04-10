---
title: "Repo Governance Evaluation Prompt"
status: active
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Repo Governance Evaluation Prompt

> 说明：本文已降级为 compatibility shim。canonical source 已迁到 [repo-governance-evaluation](../../../product/harness-operations/skills/repo-governance-evaluation/references/prompt.md)。本页只保留旧路径兼容入口，不再定义主线语义。

## Canonical Source

- [repo-governance-evaluation/SKILL.md](../../../product/harness-operations/skills/repo-governance-evaluation/SKILL.md)
- [repo-governance-evaluation/references/prompt.md](../../../product/harness-operations/skills/repo-governance-evaluation/references/prompt.md)
- [repo-governance-evaluation/references/entrypoints.md](../../../product/harness-operations/skills/repo-governance-evaluation/references/entrypoints.md)
- [docs/knowledge/README.md](../../knowledge/README.md)

> 目的：评估“仓库是否可被 AI 或非作者安全接管并持续维护”。

此文档是 repo-local prompt 模板，适合：

- `/plan` 前的治理审计
- PR 前的仓库可维护性复核
- handoff 前的仓库接管评估

## Core Prompt

```text
你是一个“工程治理审计 Agent”，需要评估一个代码仓库的维护成熟度（Repository Maintainability & Governance）。

请严格按以下步骤执行，不要跳步：

Step 1：仓库类型判断（必须）
- 只能选一个：prototype / small_product / long_term_product / platform_infrastructure
- 给出基于证据的理由

Step 2：五大维度评分（每项 0-5）
A. Baseline Hygiene
B. Change Governance（最高优先级）
C. Automation
D. Structural Clarity
E. Operational Maintainability

Step 3：输出评分
- 总分：X / 25
- 评级：22-25 工业级；16-21 可用；10-15 技术债明显；<10 不可维护

Step 4：关键证据（必须）
- 每个维度都要给文件、目录、命令或 PR 证据
- 禁止空泛评价

Step 5：高优先级问题（Top 5）
- 必须是长期维护影响最大、且可执行的问题

Step 6：30 天改进建议（最多 3 条）
- ROI 高、治理提升明显、避免重流程低收益

Step 7：AI / Harness 兼容性评估
- 任务拆分
- 局部上下文理解
- 自动验证能力
- 安全修改能力
输出：AI Compatible = YES / PARTIAL / NO

重要规则：
1) 不因文档多而高评分
2) 不因代码整齐忽略治理问题
3) Change Governance 权重最高
4) 优先识别不可维护风险
5) 结论必须有证据
```

## Rubric

### A. Baseline Hygiene

0 无 README；1 README 无用；2 能跑无结构；3 基本说明；4 清晰基线文档；5 文档代码一致且持续更新。

### B. Change Governance

0 直接 push main；1 有 PR 无 review；2 有 review 无质量；3 PR 基本说明；4 review 有效；5 保护分支、checklist、可追溯。

### C. Automation

0 无 CI；1 有但不执行；2 不阻断；3 基本 CI；4 完整 pipeline；5 CI 成为治理入口。

### D. Structural Clarity

0 一坨代码；1 混乱；2 有目录无边界；3 基本划分；4 边界清晰；5 强边界、可推理架构。

### E. Operational Maintainability

0 无法维护；1 仅原作者可改；2 成本高；3 可维护；4 易维护；5 可替换维护者。

## 本仓库对接位

- 文档模板：`docs/operations/prompt-templates/harness-contract-template.md`
- 评分脚本：
  - `python toolchain/scripts/test/governance_assess.py --input ... --output ...`
  - `python toolchain/scripts/test/repo_governance_eval.py --input ... --output ...`

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [AGENTS.md](../../../AGENTS.md)
- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
- [Review / Verify 承接位](../review-verify-handbook.md)
- [Branch / PR 治理规则](../branch-pr-governance.md)
