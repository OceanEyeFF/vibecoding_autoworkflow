# Repo Governance Evaluation Prompt + Rubric（Harness 兼容）

> 目标：评估“仓库是否可被 AI/非作者安全接管并长期维护”。
> 
> 适配：CodeX / Claude；可接 Harness；可用于 `/plan`、PR 前治理评估、仓库接管筛选。

## Core Prompt（v1）

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
- 每个维度都要给文件/PR/结构证据
- 禁止空泛评价

Step 5：高优先级问题（Top 5）
- 必须是长期维护影响最大、且可执行

Step 6：30天改进建议（最多3条）
- ROI 高、治理提升明显、避免重流程低收益

Step 7：AI/Harness 兼容性评估
- 任务拆分
- 局部上下文理解
- 自动验证能力（CI/test）
- 安全修改能力
输出：AI Compatible = YES / PARTIAL / NO

重要规则：
1) 不因文档多而高评分
2) 不因代码整齐忽略治理问题
3) Change Governance 权重最高
4) 优先识别不可维护风险
5) 结论必须有证据
```

## Rubric（0-5）

### A. Baseline Hygiene
0 无 README；1 README 无用；2 能跑无结构；3 基本说明；4 清晰基线文档；5 文档代码一致且持续更新。

### B. Change Governance（核心）
0 直接 push main；1 有 PR 无 review；2 有 review 无质量；3 PR 基本说明；4 review 有效；5 保护分支+checklist+可追溯。

### C. Automation
0 无 CI；1 有但不执行；2 不阻断；3 基本 CI；4 完整 pipeline；5 CI 成为治理入口。

### D. Structural Clarity
0 一坨代码；1 混乱；2 有目录无边界；3 基本划分；4 边界清晰；5 强边界可推理架构。

### E. Operational Maintainability
0 无法维护；1 仅原作者可改；2 成本高；3 可维护；4 易维护；5 可替换维护者。

## Harness 接入建议
- 输入样例：`.autoworkflow/state/governance-input.json`
- 工具脚本：`python tools/repo_governance_eval.py --input ... --output ...`
- 输出建议回填到：`governance-report.json` + harness contract `governance` 字段。

## 防伪闭环约束
- 评分必须附证据引用（文件/命令/PR）。
- 允许过渡期“有条件通过”，但必须设复评时间与触发条件。
- 若 `Change Governance <= 2`，不得被描述为“治理健康”。
- 若 `code` 维度不通过，整体不得通过。
