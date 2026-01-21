# AW-Kernel 项目路线图（v0.3）

> 创建时间：2026-01-06
> 最后更新：2026-01-20  
> 范围：单个小需求/小任务（建议 0.5～2 小时闭环）  
> 一句话总纲：用文档承载项目状态，用证据放行交付，用入口 Gate 把大任务挡在门外  
> 规范来源：见「二、规范性引用」  

---

## 目录（v0.3）

1. [读者指南](#一读者指南)
2. [规范性引用](#二规范性引用source-of-truth)
3. [目标与非目标](#三目标与非目标)
4. [工作流与产物契约（最小集）](#四工作流与产物契约最小集)
5. [路线图（P0/P1/P2）](#五路线图p0p1p2)
6. [成功度量与更新规则](#六成功度量与更新规则)
7. [归档：旧版路线图](#归档旧版路线图)

---

## 一、读者指南

**何时读本文件：**
- 你要确认当前优先级（P0/P1/P2）与交付标准。
- 你要新增/调整路线图条目，并希望它能被 Hooks/Skills 自动检查。

**何时不要读本文件：**
- 你要找协作基线与文档宪法：读 `CLAUDE.md` 与 `ClaudeCode协作最小共识_基准文本.md`。
- 你要找小需求流程细节：读 `AUTODEV_小需求更稳流程设计.md`。
- 你要找角色边界/输入输出/放行标准：读 `AUTODEV_小需求更稳_Agent全量定义.md`。

**本文件不承载：**
- 详细实现与长清单（高频变化内容会造成上下文污染）。
- 大规模任务规划/多里程碑长周期编排（大任务必须先过入口 Gate 拆分）。

---

## 二、规范性引用（Source of Truth）

> 下列文档是“规范性来源”，当本文件与其冲突时，以它们为准。

0. [`CLAUDE.md`](CLAUDE.md)（项目宪法：不可变事实、文档路由、协作规则）
1. [`ClaudeCode协作最小共识_基准文本.md`](ClaudeCode协作最小共识_基准文本.md)
2. [`AUTODEV_小需求更稳流程设计.md`](AUTODEV_小需求更稳流程设计.md)
3. [`AUTODEV_小需求更稳_Agent全量定义.md`](AUTODEV_小需求更稳_Agent全量定义.md)

> 资料/素材库（非规范）：
- [`AUTODEV_资料萃取_用于Agent重写与工作流实现.md`](AUTODEV_资料萃取_用于Agent重写与工作流实现.md)

---

## 三、目标与非目标

### 3.0 当前状态快照（2026-01-20）

- 核心 Agents：`Claude/agents/aw-kernel/`（6 个：ship、review、logs、clean、clarify、knowledge-researcher）
- 核心 Skills：`Claude/skills/aw-kernel/`（`autodev/`、`autodev-worktree/`；其中 v0.1 在 `Claude/skills/aw-kernel/autodev/v0.1/`）
- Hooks（已落地示例）：`.claude/hooks/agent-logger.py`（记录 Agent 执行日志）
- 命名策略：高频任务用简短命名（ship/review/logs/clean/clarify），专业领域保留完整命名（knowledge-researcher）

### 3.1 目标（只做这些）

1. **让“小需求更稳”成为默认路径**：入口规模 Gate + 2-3-1 编排 + Gate（G1/G3/G4）+ Level 0 回路（最多 3 次）。
2. **让交付“证据化”**：最小证据三件套强制产出；无证据不得宣称“编译/测试/性能通过”。
3. **让 Prompt 可压缩且不降基线**：共性硬规则下沉到 Skill/Hooks/模板，Agent 只保留职责边界与产物契约。

### 3.2 非目标（明确不做）

- 覆盖“大项目形态”的一体化规划；大任务优先走“拆分后多轮小需求”。
- 自动 Git 回退/状态文件持久化/长链路 pipeline（除非 v0.1 被验证有效且需求明确）。
- 把 ROADMAP 写成百科：实现细节进入对应 Skill/Agent/模板文档。

---

## 四、工作流与产物契约（最小集）

### 4.1 小需求默认工作流（骨架）

1. **G0：入口规模 Gate（Intake）**
   - `SizeScore(0-10)`：`<=3` 放行，`4-6` 必须拆分，`>=7` 建议拒绝/要求拆分后再进入流程。
2. **需求段（2）：Spec-Owner → Spec-Gatekeeper**
   - 产出并放行 `requirement-contract.md`（含 MUST-FOLLOW / MUST-VERIFY / 环境矩阵 / 验收）。
3. **实现段（3）：Implementer → Reviewer → Verifier**
   - 产出并放行最小证据集：`constraint-compliance.md` + `verification-report.md` + `risk-matrix.md`。
4. **交付段（1）：Finalizer**
   - 汇总交付并产出 `delivery-summary.md`（交付物清单 + 证据索引 + 风险/回退）。
5. **回路：Level 0（最多 3 次）**
   - 触发：G3 不通过 / Reviewer 给出 P0 / Verifier 验证失败。
   - 终止：P0 清零且 Gate 通过；连续失败 3 次→请求人工介入（明确卡点与下一步）。

> 运行策略：验证不可做时允许降级为 **2-2-1**，但必须显式输出“验证缺失清单 + 风险标记”，且不得宣称通过。

### 4.2 统一产物命名（强制）

- `requirement-contract.md`：需求契约（MUST-FOLLOW / MUST-VERIFY / 环境矩阵 / 验收）
- `review-findings.md`：静态审查问题清单（P0/P1/P2）
- `constraint-compliance.md`：约束符合度逐项对照
- `verification-report.md`：验证证据（命令/日志摘要/环境说明/结果）
- `risk-matrix.md`：平台/环境验证矩阵（已验证/未验证/仅推断 + 风险等级）
- `delivery-summary.md`：最终交付摘要（交付物清单 + 证据索引 + 风险/回退）
- `performance-baseline.md`：性能基准（仅当存在 MUST-MEASURE/性能目标）

### 4.3 现有 aw-kernel Agent 的角色映射（渐进式）

> 目标：先复用现有 Agent，再逐步把职责收敛到"段内单一职责"。

- `clarify` → Spec-Owner（需求契约产出）
- （新增或从现有职责拆出）→ Spec-Gatekeeper（需求门禁放行）
- `ship` → Implementer（实现，不宣称通过）
- `review` → Reviewer（对照契约挑错，输出问题清单）
- （新增/组合）→ Verifier（证据验证与最小证据集产出）
- （可复用或新增）→ Finalizer（交付整合与证据索引）

---

## 五、路线图（P0/P1/P2）

### P0（必须）：把门禁与证据落地到可自动检查

| ID | 条目 | 交付物（产物/改动） | 验收（门禁/证据） |
|---|---|---|---|
| P0-1 | 入口规模 Gate（Intake-Gatekeeper） | 在 `Claude/skills/aw-kernel/autodev/v0.1/SKILL.md` 入口加入 `SizeScore` 规则 + 拆分模板 | 大任务不进入默认路径；输出“放行/拆分/拒绝”与 ≤5 子任务验收/风险/验证方式 |
| P0-2 | 需求契约模板（Spec-Owner） | 在 `Claude/skills/aw-kernel/autodev/v0.1/` 固化 `requirement-contract.md` 模板（MUST-FOLLOW/MUST-VERIFY/环境矩阵/验收/降级策略） | G1 能检查：术语无歧义、每条 MUST-VERIFY 都有验证方法/容差/场景、矩阵明确 |
| P0-3 | 需求门禁（Spec-Gatekeeper） | 在 `Claude/skills/aw-kernel/autodev/v0.1/SKILL.md` 固化 G1 放行清单（可被 Hooks/Skill 校验） | 未通过不允许进入实现段；能输出“缺失项清单 + 补齐顺序” |
| P0-4 | 证据门禁（Verifier） | 在 `Claude/skills/aw-kernel/autodev/v0.1/SKILL.md` 强制最小证据三件套产出与校验 | G3 能检查：无证据不放行；无法验证必须显式标注原因与风险等级 |
| P0-5 | Level 0 回路（最多 3 次） | 回路触发/终止规则 + “最小修复清单”格式 | 失败→自动生成修复任务单；连续失败 3 次→明确请求人工介入 |
| P0-6 | 交付整合（Finalizer） | `delivery-summary.md` 模板（交付清单/证据索引/风险/回退/下一步） | G4 能检查：缺失产物→拒绝“完成交付”；P0 未清零→标记“未达交付门禁” |

### P1（应该）：Prompt 压缩、职责对齐、降低返工

| ID | 条目 | 交付物（产物/改动） | 验收（门禁/证据） |
|---|---|---|---|
| P1-1 | Prompt 压缩（规则下沉） | 共性硬规则下沉到 Skill/Hooks/模板；Agent Prompt 仅保留差异化职责 | Prompt 变短但“证据/诚实度/门禁”不退化；减少重复规则 |
| P1-2 | 现有 Agent 职责收敛 | 按 4.3 映射收敛边界（避免自证闭环） | Implementer 不宣称通过；Reviewer 不跑验证；Verifier 不修代码 |
| P1-3 | 缺陷结构化输出 | `review-findings.md`（P0/P1/P2）格式统一（可选补充 `bugs.json`） | Hooks/Skill 能识别 P0 并触发回路；问题能复查与复现 |

### P2（可选）：基础设施增强与可观测性

| ID | 条目 | 交付物（产物/改动） | 验收（门禁/证据） |
|---|---|---|---|
| P2-1 | Hooks 最小增稳 | `.claude/hooks/` 增加：上下文注入（inject-context）/输出验证（validate-output） | 能在不改 Agent Prompt 的情况下做“注入 + 校验 + 风险提示” |
| P2-2 | 成功度量落地 | 在日志/报告中记录证据覆盖率、P0 数量、回路次数、无法验证原因 | 能用数据回答“更稳是否有效” |

---

## 六、成功度量与更新规则

### 6.1 成功度量（验收这条路线是否有效）

- 问题发现时机：≥80% 的问题在实现段（Reviewer/Verifier）暴露，而不是拖到最终交付阶段。
- 证据覆盖率：小需求任务 100% 产出最小证据三件套。
- 诚实度：0 次“无证据宣称编译/测试/性能通过”。
- 返工成本：同类问题返工时间下降 ≥30%。

### 6.2 路线图更新规则（降低上下文污染）

1. **一条 Roadmap = 一个可交付条目**：必须写清楚交付物与验收标准；没有“怎么验收”的条目不进入 P0/P1。
2. **状态只由证据推动**：条目标记完成前，必须能给出对应产物与验证路径（或明确“无法验证”的风险说明）。
3. **细节不进 ROADMAP**：实现细节沉淀到对应 Skill/Agent/模板文档；ROADMAP 只保留“做什么/为什么/怎么验收”。

---

## 归档：旧版路线图

- 旧版路线图已归档：[`archive/work-docs/ROADMAP_legacy_v0.2.md`](archive/work-docs/ROADMAP_legacy_v0.2.md)（仅供追溯，不作为当前计划）

