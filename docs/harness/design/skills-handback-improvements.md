---
title: "Skills 层 Handback 改进方案"
status: draft
updated: 2026-04-24
owner: aw-kernel
last_verified: 2026-04-24
---

# Skills 层 Handback 改进方案

> 目的：解决 WorktrackScope → RepoScope handback 时的三类问题——基线固化缺失、artifact 输出膨胀、Goal 层缺少工程节点类型规划。

---

## 一、设计缺陷单

### P1：缺少 RepoScope Handback 的基线固化机制

| 项 | 内容 |
|---|---|
| **问题** | `WorktrackScope → RepoScope` 缺少 baseline formalization / traceability protocol。 |
| **现象** | 工作成果只停留在 working tree，回到 RepoScope 后没有形成可追溯基线。`main` 可能仍是 unborn branch，代码只存在于工作树。`close-worktrack-skill` 的 7 个收尾阶段中没有"基线固化"阶段；`repo-refresh-skill` 不验证传入基线是否可追溯。 |
| **风险** | 后续继续开发、review、回滚、比较都很弱；agent 续跑时无法定位上次工作的确切状态；working tree 变更可能被后续操作覆盖或丢失。 |
| **建议修复方向** | 1. 在 `close-worktrack-skill` 收尾阶段列表中增加"基线固化/checkpoint"阶段；2. 在"代码仓库刷新交接"中强制要求基线追溯字段；3. 在 `repo-refresh-skill` 中增加基线验收校验；4. 在 `control-state.md` 和 `snapshot-status.md` 模板中增加 `Baseline Traceability` 字段。 |
| **验收标准** | 任意 worktrack 进入 closing 后，返回的交接必须包含 `checkpoint_type`、`checkpoint_ref`、`if_no_commit_reason`（如未 commit）；`repo-refresh-skill` 对不可验证基线必须标记风险并请求审批；`control-state.md` 模板包含 `last_verified_checkpoint` 字段。 |

### P2：缺少 Artifact 输出预算与压缩规则

| 项 | 内容 |
|---|---|
| **问题** | `.aw` 下 artifact 容易重复大段状态、协议和上下文，导致人看不动、agent 续跑噪声变大、控制信号密度不足。 |
| **现象** | `gate-skill` 关卡信息包 11 个 section、判定交接 20+ 个字段；`gate-evidence.md` 模板三个 lane 每个 7 个字段；不同 skill 的交接重复包含 worktrack contract 摘要、repo snapshot 等相同上下文；空字段用占位符填充。 |
| **风险** | agent 上下文窗口被无关信息挤占；关键控制决策信息被淹没；人工审查困难；跨 skill 重复信息导致更新时不一致。 |
| **建议修复方向** | 1. 所有 artifact 模板统一引入 `Control Signal` / `Supporting Detail` 双层结构；2. 各 skill 定义输出预算（行数/字段数限制）；3. 禁止跨 artifact 平铺重复信息，改为引用路径；4. 空值使用 `N/A` 或删除占位符行。 |
| **验收标准** | 任意 skill 输出中，`Control Signal` 部分不超过 30 行；跨 artifact 重复上下文使用引用路径而非内联；空字段不生成占位符行；`harness-skill` 顶层定义全局 artifact budget 约束。 |

### P3：Goal 层缺少工程节点类型规划

| 项 | 内容 |
|---|---|
| **问题** | `set-harness-goal-skill` 生成 Goal 时只有业务/技术方向描述，没有工程层面的节点类型（feature/refactor/research/bugfix 等）规划。 |
| **原始现象** | `goal-charter.md` 模板只有 `Project Vision / Core Product Goals / Technical Direction / Success Criteria / System Invariants`，完全没有工程节点类型；`init-worktrack-skill` 无法根据类型推导 contract 中的验收标准、基线形式、gate 标准；`set-harness-goal-skill` 硬约束第 99 行过度隔离了 Goal 层与 Worktrack 层。当前实现已引入 `Engineering Node Map`，仍需确保模板、目标变更路径、校验与下游交接字段完整同步。 |
| **风险** | worktrack contract 的验收标准、基线策略、gate 判定标准都是凭空推导的；不同类型 worktrack 的 closeout 和基线固化策略不一致（P1 的根因之一）；gate 无法用类型化标准精准评估。 |
| **建议修复方向** | 1. `goal-charter.md` 模板增加 `Engineering Node Map` section；2. `set-harness-goal-skill` 工作流增加工程节点分析步骤；3. `worktrack/contract.md` 模板增加 `Node Type` section；4. `init-worktrack-skill` 从 Goal Charter 绑定节点类型；5. `gate-skill` 按节点类型调整判定标准；6. `close-worktrack-skill` 按节点类型选择基线固化策略。 |
| **验收标准** | 任意 Goal 的 `goal-charter.md` 包含 `Engineering Node Map`；任意 worktrack contract 的 `Node Type` 字段非空且与 Goal 一致；`gate-skill` 对不同类型节点应用不同判定标准；`close-worktrack-skill` 的基线固化策略与节点类型联动。 |

---

## 二、P1 详细设计：基线固化机制

### 2.1 修改清单

| # | 文件 | 修改类型 | 说明 |
|---|------|---------|------|
| P1-1 | `product/harness/skills/close-worktrack-skill/SKILL.md` | 编辑 | 增加"基线固化/checkpoint"收尾阶段 + 基线追溯交接字段 |
| P1-2 | `product/harness/skills/repo-refresh-skill/SKILL.md` | 编辑 | 增加基线验收校验 + 不可验证基线风险标记 |
| P1-3 | `product/harness/skills/set-harness-goal-skill/assets/control-state.md` | 编辑 | 增加 `Baseline Traceability` section |
| P1-4 | `product/harness/skills/set-harness-goal-skill/assets/repo/snapshot-status.md` | 编辑 | 增加 `last_verified_checkpoint` 字段 |
| P1-5 | `docs/harness/artifact/control/control-state.md` | 编辑 | 同步更新 artifact 定义 |
| P1-6 | `docs/harness/artifact/repo/snapshot-status.md` | 编辑 | 同步更新 artifact 定义 |

### 2.2 P1-1: close-worktrack-skill 修改

**收尾阶段列表增加：**

```markdown
3. 判断当前收尾阶段：
   - `准备合并请求`
   - `合并请求已开`
   - `准备合并`
   - `已合并`
   - `准备清理`
   - `准备代码仓库刷新`
   - `基线固化 / checkpoint`  ← 新增
   - `收尾被阻塞`
```

**"代码仓库刷新交接"增加基线追溯 section：**

```markdown
### 代码仓库刷新交接

- `已关闭工作追踪`
- `基准分支`
- `已接受变更摘要`
- `验证结果`
- `收尾状态`
- `可回写候选`
- **基线追溯** ← 新增 section
  - `checkpoint_type`: commit / tag / annotated-tag / stash / explicit-declaration
  - `checkpoint_ref`: SHA 或 tag 名称或 stash ref
  - `if_no_commit_reason`: 如果不形成 commit，必须显式说明原因
  - `alternative_traceability`: 替代追溯物（如 PR URL、diff patch 引用、报告路径）
- `残留风险`
- `推迟项`
- `审批请求`
```

**硬约束增加：**

```markdown
- 在返回代码仓库刷新交接前，必须确认当前工作树是否已形成可追溯基线。
- 如果工作成果未形成 git commit（或 tag、annotated stash），必须显式记录不 commit 的原因及替代追溯物。
- 不要把缺少基线追溯信息的交接当成可安全回写的状态。
```

### 2.3 P1-2: repo-refresh-skill 修改

**"代码仓库刷新信息包"增加基线验收：**

```markdown
- `基线验收状态` ← 新增
  - `incoming_checkpoint_ref`: 从 close-worktrack 交接接收的基线引用
  - `checkpoint_verified`: yes / no / deferred
  - `baseline_gap_risk`: 如果基线不可追溯，标记风险等级（low / medium / high）
```

**硬约束增加：**

```markdown
- 如果传入的代码仓库刷新交接缺少基线追溯信息，或基线不可验证，标记为基线缺失风险并回写审批请求。
- 不要从工作追踪产物直接抄写回写目标；回写目标必须关联到已验证且可追溯的基线。
```

### 2.4 P1-3: control-state.md 模板修改

在 `Handback Guard` 后增加：

```markdown
## Baseline Traceability

- last_verified_checkpoint:
- checkpoint_type:
- checkpoint_ref:
- verified_at:
- if_no_commit_reason:
- alternative_traceability:
```

### 2.5 P1-4: snapshot-status.md 模板修改

在 `Mainline Status` 下增加：

```markdown
## Mainline Status

- branch:
- last_verified_checkpoint:  ← 新增
- checkpoint_ref:            ← 新增
- checkpoint_type:           ← 新增
```

### 2.6 P1-5 / P1-6: artifact 定义文档同步

同步更新 `docs/harness/artifact/control/control-state.md` 和 `docs/harness/artifact/repo/snapshot-status.md` 中的最小字段定义。

---

## 三、P2 详细设计：Artifact 输出预算

### 3.1 修改清单

| # | 文件 | 修改类型 | 说明 |
|---|------|---------|------|
| P2-1 | `product/harness/skills/harness-skill/SKILL.md` | 编辑 | 顶层增加全局 Artifact Output Budget 约束 |
| P2-2 | `product/harness/skills/gate-skill/SKILL.md` | 编辑 | 增加输出预算约束 + 引用而非平铺规则 |
| P2-3 | `product/harness/skills/close-worktrack-skill/SKILL.md` | 编辑 | 增加输出预算约束 |
| P2-4 | `product/harness/skills/repo-refresh-skill/SKILL.md` | 编辑 | 增加输出预算约束 |
| P2-5 | `product/harness/skills/set-harness-goal-skill/assets/worktrack/gate-evidence.md` | 编辑 | 引入双层结构 |
| P2-6 | `product/harness/skills/set-harness-goal-skill/assets/worktrack/contract.md` | 编辑 | 引入双层结构 |
| P2-7 | `product/harness/skills/set-harness-goal-skill/assets/worktrack/plan-task-queue.md` | 编辑 | 引入双层结构 |

### 3.2 P2-1: harness-skill 顶层预算

在 skill 文档中增加全局约束 section：

```markdown
## Artifact Output Budget

所有 skill 产出的 artifact 必须遵守以下全局约束：

1. **控制结论优先**：影响下一动作决策的信息放在 `Control Signal` 层，每行不超过 80 字符，总长度不超过 30 行。
2. **细节下沉**：完整证据、日志、原始输出放在 `Supporting Detail` 层。
3. **禁止平铺重复**：已在其他 artifact 中记录的信息，使用引用（文件路径 + section）而不是内联全文复制。
4. **空值压缩**：无实质内容的字段使用 `N/A`，删除占位符行（如 `- ` 或 `待填写`）。
5. **总预算**：单个 `.aw/` 目录下所有文件单次更新后的净增量不超过 100 行（除非有明确的 large-artifact 豁免标记）。
6. **引用格式**：引用其他 artifact 时使用 `[artifact-path#section]` 格式，例如 `[.aw/worktrack/contract.md#Task Goal]`。
```

### 3.3 P2-2 ~ P2-4: 各 skill 输出预算

以 `gate-skill` 为例：

```markdown
## 输出预算

- `Control Signal` 总长度不超过 30 行
- `Supporting Detail` 中，每个证据维度摘要不超过 10 行
- 重复性上下文（如 worktrack contract 摘要、repo snapshot 等）引用文件路径，不要内联全文
- 如果某个字段无实质内容，使用 `N/A` 或省略，不要用占位符填充
- `gate-evidence.md` 更新时，优先追加到 `Control Signal` 层；`Supporting Detail` 层只在首次生成时填充完整骨架，后续更新只追加变更
```

### 3.4 P2-5 ~ P2-7: Artifact 模板双层结构

以 `gate-evidence.md` 为例，每个 section 拆分为双层：

```markdown
## Review Lane

### Control Signal
- confidence:
- ready_for_gate:
- residual_risks:

### Supporting Detail
- input_ref:
- freshness:
- missing_evidence:
- upstream_constraint_signals:
- low_severity_absorption_applied:
```

**迁移策略：** 不要求一次性重写所有历史 artifact。新模板作为"目标格式"，运行时逐步迁移。现有 `.aw/` 下的 artifact 在下次更新时按新格式写入。

---

## 四、P3 详细设计：工程节点类型

### 4.1 修改清单

| # | 文件 | 修改类型 | 说明 |
|---|------|---------|------|
| P3-1 | `product/harness/skills/set-harness-goal-skill/assets/goal-charter.md` | 编辑 | 增加 `Engineering Node Map` section |
| P3-2 | `product/harness/skills/set-harness-goal-skill/SKILL.md` | 编辑 | 工作流增加工程节点分析；更新过度隔离约束 |
| P3-3 | `product/harness/skills/set-harness-goal-skill/assets/worktrack/contract.md` | 编辑 | 增加 `Node Type` section |
| P3-4 | `product/harness/skills/init-worktrack-skill/SKILL.md` | 编辑 | 增加节点类型绑定步骤 |
| P3-5 | `product/harness/skills/gate-skill/SKILL.md` | 编辑 | 增加按节点类型的判定差异 |
| P3-6 | `product/harness/skills/close-worktrack-skill/SKILL.md` | 编辑 | 基线固化阶段与节点类型联动 |
| P3-7 | `docs/harness/artifact/repo/goal-charter.md` | 编辑 | 同步更新 artifact 定义 |
| P3-8 | `docs/harness/artifact/worktrack/contract.md` | 编辑 | 同步更新 artifact 定义 |

### 4.2 P3-1: goal-charter.md 模板修改

在 `Technical Direction` 之后增加：

```markdown
## Engineering Node Map

> 本 Goal 涉及的工程节点类型规划，供 `init-worktrack-skill` 在拆分 worktrack 时参考。
> 不是 worktrack 拆分本身，而是定义"这个 Goal 下会产生哪些类型的工程节点"及其约束。

### Node Type Registry

可复用的节点类型定义（全局参考，非必填）：

| type | merge_required | baseline_form | gate_criteria | if_interrupted_strategy | 说明 |
|------|---------------|---------------|---------------|-------------------------|------|
| `feature` | yes | commit-on-feature-branch | implementation + validation + policy | checkpoint-or-recover | 新功能开发 |
| `refactor` | yes | commit-on-refactor-branch | validation + policy | checkpoint-or-rollback | 重构，不改变外部行为 |
| `research` | no | annotated-tag-or-report | review-only | preserve-report-and-stop | 调研/探针，产出可能不可合并 |
| `bugfix` | yes | commit-on-bugfix-branch | implementation + validation + policy | checkpoint-or-rollback | 缺陷修复 |
| `docs` | yes | commit-on-docs-branch | review + policy | checkpoint-or-recover | 文档更新 |
| `config` | yes | commit-on-config-branch | validation + policy | checkpoint-or-rollback | 配置/部署变更 |
| `test` | yes | commit-on-test-branch | validation + policy | checkpoint-or-recover | 专项测试 |

### This Goal's Node Types

> 列出本 Goal 预期会涉及的节点类型：

- type:
  - expected_count:
  - merge_required:
  - baseline_form:
  - gate_criteria:
  - if_interrupted_strategy:

### Node Dependency Graph

> 如果有明确的节点间依赖关系：

- source_type → target_type (reason)

### Default Baseline Policy

- if_worktrack_interrupted: stash-and-tag / commit-with-note / explicit-declaration
- if_no_merge: document-alternative-traceability
```

### 4.3 P3-2: set-harness-goal-skill 修改

**工作流第 2 步增加：**

```markdown
2. **分析用户需求**
   - 读取用户提供的自然语言需求描述
   - 识别核心目标、范围边界、技术约束、成功标准
   - 识别可分解的子系统或阶段（供后续 worktrack 拆分参考）
   - **识别预期的工程节点类型**：分析需求中隐含的功能开发、重构、调研、修复等工程性质
   - **为每个节点类型定义基线策略**：commit 形式、merge 要求、gate 标准、中断处理策略
   - 将工程节点类型填入 `Engineering Node Map`
```

**工作流第 3 步更新：**

```markdown
3. **生成 `goal-charter.md`**
   - 将分析结果填入标准 `Goal Charter` 格式
   - 包含：Project Vision、Core Product Goals、Technical Direction、Success Criteria、System Invariants、Engineering Node Map
   - **不**在 goal charter 中指定具体的 worktrack 拆分方式；worktrack 拆分属于 `init-worktrack-skill` 的职责
```

**硬约束更新（替换第 99 行）：**

```markdown
- 不在 goal charter 中指定具体的 worktrack 拆分方式；worktrack 拆分是 `init-worktrack-skill` 的职责
- **但必须在 goal charter 中定义 Engineering Node Map，为 worktrack 初始化提供类型化约束**
```

### 4.4 P3-3: contract.md 模板修改

在 Metadata 后增加：

```markdown
## Node Type

- type:  # feature / refactor / research / bugfix / docs / config / test
- source_from_goal_charter:  # 引用 goal-charter.md 中的 Engineering Node Map
- baseline_form:  # commit / tag / stash / explicit-declaration
- merge_required:  # yes / no
- gate_criteria:  # 本 worktrack 适用的判定标准组合
- if_interrupted_strategy:  # 与 goal charter 中的 Default Baseline Policy 对齐
```

### 4.5 P3-4: init-worktrack-skill 修改

**工作流第 1 步更新：**

```markdown
1. 载入当前 `Harness 控制状态`、`Goal Charter` 中的 `Engineering Node Map`、与初始化所需的最小代码仓库/工作追踪产物。
```

**工作流第 6 步增加：**

```markdown
6. 构建或刷新一份 `工作追踪约定`；有需要时，让草稿与 `templates/contract.template.md` 对齐。
   - **从 Goal Charter 的 Engineering Node Map 中确定本 worktrack 的节点类型**
   - **根据节点类型填充 contract 中的类型化字段**：baseline_form、merge_required、gate_criteria、if_interrupted_strategy
   - 如果 Goal Charter 未定义 Engineering Node Map，标记为缺失风险并在初始化结果中暴露
```

**预期输出增加字段：**

```markdown
- `节点类型`
- `基线形式`
- `合并要求`
- `判定标准`
```

### 4.6 P3-5: gate-skill 修改

在"关卡判定规则"中增加类型化判定：

```markdown
### 按节点类型的判定差异

- `feature` 节点：三个层面全部通过才允许推进
- `refactor` 节点：实现层面允许"无新增 surface"，验证层面必须全部通过
- `research` 节点：只要求 review 层面通过，validation 层面为可选；产出不可合并时 gate 标准自动降级
- `bugfix` 节点：实现 + validation 必须通过，policy 层面允许"修复性例外"
- `docs` 节点：review + policy 通过即可
- `config` 节点：validation 层面必须覆盖配置正确性，policy 层面覆盖规则合规
- `test` 节点：validation 层面为核心，implementation 层面为辅助
```

### 4.7 P3-6: close-worktrack-skill 基线固化与节点类型联动

在"基线固化/checkpoint"阶段中，按节点类型选择策略：

```markdown
### 基线固化策略（按节点类型）

| 节点类型 | baseline_form | 固化动作 |
|---------|--------------|---------|
| `feature` | commit-on-feature-branch | PR → merge → git commit 基线 |
| `refactor` | commit-on-refactor-branch | PR → merge → git commit 基线 |
| `bugfix` | commit-on-bugfix-branch | PR → merge → git commit 基线 |
| `docs` | commit-on-docs-branch | PR → merge → git commit 基线 |
| `config` | commit-on-config-branch | PR → merge → git commit 基线 |
| `test` | commit-on-test-branch | PR → merge → git commit 基线 |
| `research` | annotated-tag-or-report | 不 merge → git annotated tag + 报告文件 → 标记替代追溯物 |

如果节点类型未定义，fallback 到最保守策略：要求 commit 基线，否则显式声明替代追溯物。
```

### 4.8 P3-7 / P3-8: artifact 定义文档同步

同步更新 `docs/harness/artifact/repo/goal-charter.md` 和 `docs/harness/artifact/worktrack/contract.md` 中的最小字段定义。

---

## 五、实施顺序建议

### Phase 1: 模板层（可独立落地，不依赖 skill 逻辑）

1. P1-3: control-state.md 模板增加 Baseline Traceability
2. P1-4: snapshot-status.md 模板增加 checkpoint 字段
3. P2-5~P2-7: worktrack artifact 模板引入双层结构
4. P3-1: goal-charter.md 模板增加 Engineering Node Map
5. P3-3: contract.md 模板增加 Node Type
6. P1-5/P1-6/P3-7/P3-8: artifact 定义文档同步

→ 新部署的 .aw/ 目录已包含改进后的模板骨架。

### Phase 2: Skill 层（依赖模板层完成）

7. P1-1: close-worktrack-skill 增加基线固化阶段
8. P1-2: repo-refresh-skill 增加基线验收
9. P3-2: set-harness-goal-skill 增加工程节点分析
10. P3-4: init-worktrack-skill 增加节点类型绑定
11. P3-5: gate-skill 增加类型化判定
12. P3-6: close-worktrack-skill 基线固化与类型联动
13. P2-1: harness-skill 增加全局 artifact budget
14. P2-2~P2-4: 各 skill 增加输出预算约束

→ 运行时行为按新规范执行。

---

## 六、联动效果

P3（工程节点类型）→ worktrack contract baseline_form 明确使 P1 有据可依、gate 判定类型化减少 P2 通用最大集输出、closeout 策略差异化；P1（基线固化）→ checkpoint_ref 写入 control-state 使 P2 后续 skill 可引用而非平铺；P2（输出预算）→ 引用格式标准化使 P1 基线信息跨 artifact 传递更轻量。
