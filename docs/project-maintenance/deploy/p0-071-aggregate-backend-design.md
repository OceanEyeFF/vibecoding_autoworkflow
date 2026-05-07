---
title: "P0-071 Aggregate Backend Multi-Distribution — Design Phase Research Report"
status: draft
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---

# P0-071 Aggregate Backend Multi-Distribution — Design Phase Research Report

> **Status：design-phase 草案。** 本报告整合 WT-20260507-aggregate-backend-design 工作追踪下 5 个 research SubAgent（SA-A~SA-E）的 deliverables，是 implementation phase 的输入。本报告**不修改**真相层文档（`distribution-entrypoint-contract.md` / `deploy-mapping-spec.md` / `goal-charter.md`），不修改 `aw-installer.js`，不修改 `path_safety_policy.json`。implementation phase 必须经 programmer 新一轮批准后才可启动。
>
> 完整 SubAgent 草案落点：`.aw/worktrack/research-deliverables/sa-{a,b,c,d,e}-*.md`（控制面工作区，gitignored）。本报告提取关键决议并提供整合视图；详细论证、表格、消息草案见各 SA 草案。

---

## 1. Executive Summary

P0-071 在 `aw-installer` 命令面上引入 **aggregate backend mode**，让 operator 用一次命令调用同时完成 `agents` + `claude` 双分发安装。design phase 的 7 项核心决议如下：

| 决议域 | 决议 | 来源 |
|---|---|---|
| 命令面 protocol | **`--backend bundle` enum 扩展**（候选 A） | SA-A |
| 多 backend 事务语义 | **per-command hybrid**：写前 all-or-nothing；写时 each-independent；只读 collect-then-report | SA-B |
| 跨 backend 回滚策略 | **不做跨 backend 回滚**（与 single-backend 现行合同保持一致） | SA-B §4 |
| 双根 trust boundary | **fail-closed on writes；prune 顺序 agents→claude；verify collect-then-report** | SA-C |
| `path_safety_policy.json` 修订 | **不修订**（policy 字段是路径级全局约束，与 backend 无关） | SA-C §5 |
| 合同修订形态 | `distribution-entrypoint-contract.md` / `deploy-mapping-spec.md` 仅做 **additive 扩展**（新增 aggregate 小节，不动既有单 backend 条款） | SA-D D-1 / D-2 |
| Charter 张力 | `bundle` 是 **operator 便利层**，不是新 lane、不是新 Engineering Node Map 节点类、不改变两 distribution 的真相层分离；**`.aw/goal-charter.md` 不需要修订** | SA-D D-3 |
| TUI/CLI 等价 | **TUI 主菜单 backend 字段三选一 mode-switch + args 数组动态拼接**；TUI 仅作为 args 数组 widget 化呈现，dispatcher 层与 CLI 共享同一入口 | SA-E |
| 测试 surface | 既有 80 测试中 **24 must mirror / 19 should mirror / 37 should-not mirror**；新增 **22 个 multi-backend 专属用例** | SA-E |

**最强 design rationale**：aggregate mode 必须是对现有 single-backend 合同的**最小 additive 扩展**。任何"比 single-backend 更强的合同"（例如跨 backend 全量回滚、双根 lane 重定义、policy schema 多根字段、TUI 独立 bundle 子菜单）都被 design 阶段显式拒绝，因为它们违反 charter "wrapper 不能改变 deploy 语义"的硬不变量，并制造 single-backend / aggregate 的双语义维护负担。

---

## 2. 命令面 Protocol 决议（来自 SA-A）

### 2.1 推荐方案

**`--backend bundle` enum 扩展**：在现有 `--backend` flag 上新增 `bundle` 枚举值，与 `agents`、`claude` 平级；`bundle` 触发 dispatcher 内部的双 context 顺序编排。

### 2.2 关键决策依据

- **既有 80 测试中 30+ 处 `{ backend: "agents", ... }` deepEqual 断言完全不变**：bundle 是新 valid 枚举值，agents/claude 仍是 valid 单值，9 个 `parseNodeXxxArgs` 测试 block 全部不需要重写。
- **dispatcher 拓扑零变化**：保持 9 parser → runNodeXxx → backend handler 形态，仅在 `backendAllowed` 与 `parsedBackendRoots` / `targetRootForBackend` 上加 bundle 分支。
- **TUI 等价友好**：`Backend:` 行天然支持三值显示，args 数组拼接是字符串替换。

### 2.3 拒绝候选

| 候选 | 拒绝理由 |
|---|---|
| **B：`--backend agents,claude` 多值列表** | backend 字段从 string 变成 list/union，连锁波及 9 个 `parseNodeXxxArgs` 测试 block 中 30+ 处 deepEqual 断言；引入"逐项解析逻辑混入 backend 字段"风险 |
| **C：新增 `bundle` 子命令** | 命令面分叉，需新建一组 `bundle install` / `bundle update` / `bundle verify` 子命令；与现行单一动词 + `--backend` flag 形态拓扑不一致；CLI ↔ TUI 等价复杂度上升 |

### 2.4 全文

详见 `.aw/worktrack/research-deliverables/sa-a-command-protocol-decision.md`（282 行；含 5 维度 × 3 候选评估、全 trade-off 表、backward-compat 影响清单）。

---

## 3. 多 Backend 事务语义决议（来自 SA-B）

### 3.1 选定模型

**Per-command hybrid**：
- **写前预扫描类**（`check_paths_exist` / `install` / `update --yes` 预检）：**all-or-nothing pre-write**，任一根冲突 fail-fast，零写入。
- **只读类**（`verify` / `diagnose` / `update --json` / `update` dry-run）：**collect-then-report each-independent**，两 backend 都跑完，issues 合并；exit code 在任一 backend 报 issue 时非零。
- **写时执行类**（`install` 已 mkdirSync 后、`prune --all` 删除阶段、`update --yes` apply 阶段）：**no-rollback each-independent with partial-completion surface**，跨 backend 不做反向回滚。

### 3.2 6 命令完整失败口径表

| command | transaction_model | short_circuit | rollback | partial_completion_surface |
|---|---|---|---|---|
| `install` | hybrid | pre-write fail-fast；write first-fail-stop | none | exit 1 + `[aggregate] partial install: agents=ok, claude=failed` |
| `update` (dry-run) | each-independent collect | 不短路 | N/A 只读 | exit 由任一 `blocking_issue_count > 0` 决定 |
| `update --yes` | hybrid | pre-check fail-fast；apply first-fail-stop | none | exit 1 + `[aggregate] partial update: agents applied (verified), claude failed at <stage>` |
| `verify` | each-independent collect | 不短路 | N/A 只读 | 按 backend 分组输出，每根一段 issue list |
| `prune --all` | hybrid | pre-check fail-fast；delete first-fail-stop | none | exit 1 + `[aggregate] partial prune: agents removed N dir(s) before failure, claude not started` |
| `check_paths_exist` | all-or-nothing pre-scan (合并双根) | 不短路（只读） | N/A 只读 | exit 由任一根冲突决定 |
| `diagnose` | each-independent collect | 不短路 | N/A 只读 | exit 0；JSON 输出含 `agents` / `claude` 两 backend section |

### 3.3 关键 rollback 决议

**aggregate `install` 时 agents 写入成功、claude 写入失败 → 不回滚 agents**。
- agents 已写入的所有文件、目录、marker **完整保留**
- claude 半成品也**不自动 prune**
- operator 通过 stderr 中的 recovery hint 显式选择补救动作（`prune --backend claude --all` → `install --backend claude` → `verify`）

理由：现有 single-backend `installBackendPayloads`（aw-installer.js 2236-2310）与 `applyUpdateContext`（3076-3090）本身**没有写后回滚合同**；aggregate 引入跨 backend 回滚 = 比 single-backend 更强的合同 = 违反"wrapper 不能改变 deploy 语义"硬约束。

### 3.4 verify 短路口径

**collect-then-report，不 fail-fast**。verify 是只读诊断工具，operator 想一次拿到双根全部 drift，不希望第一根失败时对第二根失语。

### 3.5 全文

详见 `.aw/worktrack/research-deliverables/sa-b-transaction-semantics.md`（380 行；含完整 6 命令决议表 + 3 个具体 rollback 场景的"保留 / 不保留"清单）。

---

## 4. 双根 Trust Boundary 扩展规则（来自 SA-C）

### 4.1 三项 top-level 决策

1. **双根冲突短路 fail-closed**：写入路径（`install` / `update --yes` / `check_paths_exist`）下，任一根触发既有 trust boundary 短路条件（unrecognized-target-directory / wrong-target-root-type / foreign-managed-directory / payload-contract-invalid 等）→ aggregate 立即停止，不允许"R_a 失败但 R_c 继续"。
2. **`prune --all` 顺序 agents → claude**：固定顺序（按 backend ASCII 排序），前置/删除阶段任一失败即停，**不做跨根回滚**；删除是 marker-gated idempotent，不撤销重建。
3. **`verify` collect-then-report，但 exit code fail-fast**：两根都执行 `verifyBackend`，issues 合并汇报；任一根有 issue → aggregate exit 非零。

### 4.2 `path_safety_policy.json` 不修订

policy 4 字段（`exact_sensitive_target_repo_roots` / `recursive_sensitive_target_repo_roots` / `home_relative_recursive_sensitive_target_repo_roots` / `allowed_target_repo_root_prefixes`）都是**路径级全局约束**，与 backend 无关；aggregate dispatcher 复用既有 `validateTargetRepoRoot` / `validateSourceRepoRoot` 即可。新增 `multi-root` 类字段无可作用对象，反而降低 schema 清晰度。**trust boundary 增量全部落在 aw-installer.js dispatcher 层，不落在 policy schema**。

### 4.3 双根冲突合法性真值表（写入路径摘要）

完整真值表见 SA-C §2.2 表 A（12 行 × 写入命令）/ 表 B（8 行 × prune 命令）/ 表 C（9 行 × verify 命令）。关键合法/非法分界：

| 状态分类 | 写入路径 |
|---|---|
| 两根都 clean / 两根 marker 一致 | legal |
| 任一根 unrecognized-target-directory / wrong-target-root-type / EACCES | illegal，fail-closed |
| 双根 marker 但 binding 漂移（`marker.skill_id` 漂移、`marker.backend` mismatch） | illegal，aggregate 在到达对端前先列出 issue |
| missing-target-root（root 目录不存在） | legal（仅 install / update --yes 路径，由 `ensureInstallTargetRoot` 创建） |

### 4.4 新引入的 4 个 edge case

- **E1**：cross-marker 误置目录（claude marker 出现在 .agents/skills 下）→ prune 不删（既有逻辑），aggregate stderr 警告
- **E2**：双 override 跨 prefix（`--agents-root` 与 `--claude-root` 指向同一 prefix 但不同 sensitive root）→ aggregate context 构造阶段 reject
- **E3**：override 至 sensitive root（任一根落入 home-relative recursive sensitive 集合）→ `validateTargetRepoRoot` 抛出
- **E4**：一端 adapter skills 为空（agents adapter 没有 skill 但 claude 有）→ 视该端 install 为 no-op，aggregate 仍执行另一根

### 4.5 全文

详见 `.aw/worktrack/research-deliverables/sa-c-trust-boundary.md`（329 行；含 4 张完整真值表 + 11 节决议 + operator-facing 错误消息草案）。

---

## 5. 合同修订草案（来自 SA-D D-1 / D-2）

### 5.1 修订原则（载入合同的硬约束）

1. **既有单 backend 合同条款一字不改** — agents 与 claude 单值 backend 在所有命令面保持现行语义；本修订仅作 additive 扩展。
2. **聚合 mode 的合同条款单独成节** — 用专门的 `Aggregate Backend (--backend bundle)` 小节集中表达，避免在既有命令面合同表内塞入歧义脚注。
3. **回滚策略显式标注** — 合同明确 `per-backend each-independent on writes; no cross-backend rollback`，operator 与下游 implementation 都不得假设跨根原子。
4. **错误信号双前缀化** — 所有 aggregate 模式输出加 `[backend=<name>]` 前缀，消除混合时的归因歧义。

### 5.2 D-1：`distribution-entrypoint-contract.md` 修订

涉及 6 个 section：
- **Frontmatter**：`updated` / `last_verified` 由 implementation phase 落地日填入
- **§ 当前 package/runtime surface**：补一句"`bundle` 作为聚合 enum 值，等价于在两个 distribution 上同时执行同一 verb"
- **§ 命令面合同**：既有 6 行不变；新增 7 行 "Aggregate Mode Clauses"
- **新增 § Aggregate Backend (`--backend bundle`)**：dispatch surface / transaction semantics / dual-root failure short-circuit 三段
- **§ CLI / TUI 不变量**：新增 1 条（aggregate stderr/stdout backend prefix；TUI 必须保留同前缀）
- **§ 停止线**：不变

修订**不**改写："CLI 是稳定脚本接口"、"wrapper 不能改变 deploy 语义"、"TUI 不得拥有独立于 CLI 的 install/update 语义"、"`diagnose` 不是安装成功证明"、"wrapper 不得把 deploy target 当成 source of truth"。

### 5.3 D-2：`deploy-mapping-spec.md` 修订

- **既有 agents / claude mapping 行不动**
- target 命名表新增 `bundle` 行，**显式声明**："agents 端 = `aw-{skill_id}` + claude 端 = `{skill_id}` 同时实例化"，避免下游推断歧义
- `target_dir` 唯一性条款在最小字段表与不变量段双处补 per-root 澄清

### 5.4 修订实施 quality bar

implementation phase 套用本草案时可直接 copy/paste：所有 D-1/D-2 修订都以 unified-diff 风格 + before/after 对照表呈现。

### 5.5 全文

- D-1：`.aw/worktrack/research-deliverables/sa-d-distribution-entrypoint-contract-revision.md`（486 行）
- D-2：`.aw/worktrack/research-deliverables/sa-d-deploy-mapping-spec-revision.md`（453 行）

---

## 6. Charter 张力声明（来自 SA-D D-3）

### 6.1 一句话声明

> 聚合 backend (`--backend bundle`) 是 `aw-installer` 在 operator 视角的便利层；它不重定义 mainline lane 与 compatibility lane 的关系、不引入新的 Engineering Node Map 节点类，也不改变 `agents` 与 `claude` 在真相层的分发分离。

### 6.2 三段式承诺

**它是什么**：`aw-installer` 的 dispatcher control-plane 行为，把"运维者要分别敲两次单 backend 命令"工序合并为"敲一次 aggregate 命令"。`npx aw-installer install --backend bundle` 等价于先 `--backend agents` 再 `--backend claude`，但带 fail-closed 写前预扫描与统一 stderr 归因前缀。

**它不是什么**：
- **不是新 distribution lane**：mainline lane（Node/npx）与 compatibility lane（Claude skills）不变；`bundle` 是 mainline 与 compatibility 的**操作合并视图**
- **不是 Engineering Node Map 新节点类**：implementation phase 用现有 `feature` 节点类承担
- **不改变两 distribution 的真相层分离**：`.agents/skills/` 与 `.claude/skills/` 仍是独立 deploy targets；marker.backend、source binding、verify boundary、prune boundary 全部独立

**它如何与 charter 共存**：

```
charter:
  mainline lane     = Node/npx, agents distribution, P0 consumer
  compatibility lane = Claude skills distribution, slower lane

aggregate (bundle) = mainline.write() ⊕ compatibility.write()
                     where ⊕ is "同时调度并保留各自合同"
                     not "merge into one lane"
                     not "redefine lane class"
                     not "shift compatibility lane to P0"
```

`bundle` partial-completion 模式（agents 成功 / claude 失败）正是 charter "do not let Claude-specific packaging block the Node/npx mainline" 的运行时表达。

### 6.3 关键承诺：`.aw/goal-charter.md` 不需要修订

charter 的 Project Vision、Core Product Goals、Technical Direction、System Invariants、Engineering Node Map 5 大段落均未被 P0-071 触动；本声明的存在恰恰用来证明 ChangeGoal 流程不需要被触发。

### 6.4 全文

详见 `.aw/worktrack/research-deliverables/sa-d-charter-tension-declaration.md`（209 行；含 charter 5 大段落逐条对照）。

---

## 7. TUI / CLI 双面映射 + 测试 Surface（来自 SA-E）

### 7.1 TUI 映射方案

**主菜单 `Backend:` 行升级为可切换 backend 选择项（agents / claude / bundle 三选一）**，`b` / `B` 键作为 mode-switch 触发器：

```
AW Installer
Backend: bundle  (press b to switch: agents / claude / bundle)

1. Guided update flow
2. Diagnose current install
3. Verify current install
4. Show update dry-run plan
5. Show CLI help
6. Exit
```

不引入新的子菜单或独立的"bundle operations"层。`currentBackend` 变量初值 `agents`（保持向后兼容）；所有菜单项的 `runNodeOwned([verb, "--backend", currentBackend, ...])` 调用以字符串拼接形式传入 dispatcher。

### 7.2 CLI ↔ TUI 等价证明

- **TUI 是 args 数组的 widget 化呈现**：CLI 与 TUI 走完全相同的 dispatcher 入口
- **等价关系**：args 数组相同 → 行为相同（同一 path-safety scan / 同一 transaction model from SA-B / 同一 trust boundary from SA-C）
- **partial-completion 失败 UX**：TUI 在 guided update flow 中显式标注 "Step N: ..., each-independent across both roots"；具体 stderr 内容由 dispatcher 透明承担

### 7.3 测试 Surface 设计

| 类别 | 数量 | 说明 |
|---|---|---|
| **既有测试 must mirror** | 24 | parser tests for `--backend bundle`、install/update/verify under bundle |
| **既有测试 should mirror** | 19 | additional confidence cases |
| **既有测试 should NOT mirror** | 37 | github source / Python reference parity / 单元工具 / single-backend 专属语义 |
| **新增 multi-backend 专属用例** | 22 | 7 类：parser 5 / dual-root 冲突 3 / partial completion 4 / dispatcher 等价 3 / TUI ↔ CLI 等价 4 / recovery hint 2 / 边界 fallback 1 |

**测试覆盖矩阵**：6 verbs（install / update / verify / prune --all / check_paths_exist / diagnose）× 3 backends（agents / claude / bundle）= 18 cells；每 cell 标注 P/D/S/F 四类（parser / dispatch / success / failure）。bundle 列每 cell 显式标注 SA-B / SA-C / SA-A 决议带来的额外覆盖项。

### 7.4 关键 test-surface 决策

**partial-completion stderr 必须以精确字面串测试锁定**（如 `[aggregate] partial install: agents=ok, claude=failed`），而非仅 regex 包含校验。理由：该字符串是 SA-B hybrid 事务模型对 operator 的**唯一 recovery 入口**，输出漂移会让 recovery 路径失语。

### 7.5 全文

详见 `.aw/worktrack/research-deliverables/sa-e-tui-cli-mapping-and-test-surface.md`（525 行；含 22 用例完整描述 + 18-cell 覆盖矩阵 + acceptance question 锚点）。

---

## 8. Implementation Phase 路线图与 Boundary 提示

### 8.1 implementation phase 启动条件

- **必须经 programmer 新一轮批准**（design Gate review 通过 + truth-layer 写入授权 + aw-installer.js 实现授权）
- 当前 control-state 明确 `aw_installer_js_write_allowed: false` 与 `truth_layer_contract_write_allowed: false`，design phase 完结时这两个开关需要 programmer 显式翻转

### 8.2 implementation phase 推荐切片（节点类 = `feature`）

| 切片 | 改动面 | 验证 |
|---|---|---|
| **切片 1：parser + dispatcher 扩展** | aw-installer.js `backendAllowed` / `parsedBackendRoots` / `targetRootForBackend` / `runNodeXxx` 9 处 | parser test mirror 24 处；新增 parser 5 用例 |
| **切片 2：聚合 dispatcher 实现** | aw-installer.js 新增 `installBundle` / `verifyBundle` / `pruneBundle` / `diagnoseBundle` / `checkPathsExistBundle` 等聚合执行函数 | dispatcher 等价 3 用例；dual-root 冲突 3 用例 |
| **切片 3：TUI mode-switch** | aw-installer.js `runTui` Backend 行升级 + `b` 键处理 + args 数组动态拼接 | TUI ↔ CLI 等价 4 用例 |
| **切片 4：partial-completion stderr 与 recovery hint** | aw-installer.js stderr 输出 + recovery hint 文案 | partial completion 4 用例 + recovery hint 2 用例（精确字面串锁定） |
| **切片 5：合同回写真相层** | `distribution-entrypoint-contract.md` / `deploy-mapping-spec.md` 套用 D-1 / D-2 修订草案 | 治理检查 folder_logic / path_governance / governance_semantic |

### 8.3 implementation phase boundary 硬约束（来自 design phase 决议）

- **不引入跨 backend 回滚** — aggregate `install` / `update --yes` / `prune --all` 不允许撤销已写入 / 已删除的内容
- **不修改 `path_safety_policy.json`** — 所有 trust boundary 增量都在 dispatcher 层
- **不修改 `.aw/goal-charter.md`** — aggregate 是便利层，不是 lane 重定义
- **TUI 不得引入独立 bundle 子菜单或独立事务执行流** — TUI 只是 args 数组 widget 化呈现
- **partial-completion stderr 必须精确字面串测试** — 不允许 regex 包含校验
- **既有 80 测试 30+ 处 deepEqual 断言不能改写** — 仅追加 mirror 与新增用例
- **`bundle` 与 github source 不兼容** — `--backend bundle --source github` 必须 reject（错误消息 `--backend bundle is not supported with --source github; bundle requires --source package`）

### 8.4 implementation phase 风险

- **partial-completion UX 设计偏差** — implementation phase 必须严格按 SA-B §3 全表 7 行实施，不允许"agents 成功就当全成功" 或反向；validation 矩阵需要覆盖每个 partial 状态
- **TUI 现有 6 菜单项硬编码 `--backend agents` 改造遗漏** — implementation 切片 3 必须把 aw-installer.js 第 3422 / 3437 / 3450 / 3486 / 3489 / 3492 行 6 处全部改为动态 `currentBackend`，遗漏会导致 TUI agents 模式 bypass `currentBackend` 选择
- **dispatcher 内 sequential 顺序遗漏** — SA-C §3 prune 顺序固定 agents → claude，install / update --yes 当前 SA-B 决议未硬绑定顺序；implementation phase 必须显式选择并固化顺序，避免运行时不确定性

---

## 9. Design Gate 准备

### 9.1 acceptance criteria 自检（worktrack contract §Acceptance Criteria）

| # | 标准 | 满足情况 | 证据 |
|---|---|---|---|
| 1 | 命名与命令面 protocol 决议明确（推荐方案 + 至少 2 项替代分析 + 决策依据） | ✅ | §2 + SA-A 全文 |
| 2 | 多 backend 事务语义决议给出明确口径（含失败回滚清单） | ✅ | §3 + SA-B 全文 |
| 3 | trust boundary 扩展规则草案能回答 3 项关键问题 | ✅ | §4 + SA-C 全文（4 张真值表） |
| 4 | distribution-entrypoint-contract.md 与 deploy-mapping-spec.md 修订草案达到"实现 phase 可直接接管"质量 | ✅ | §5 + SA-D D-1 / D-2 全文（unified-diff 风格） |
| 5 | charter 张力声明明确"聚合 backend 是 operator 便利层而非 lane 重定义" | ✅ | §6 + SA-D D-3 全文 |
| 6 | TUI / CLI 等价映射方案能回答"如何在 CLI 与 TUI 表达同一聚合操作" | ✅ | §7 + SA-E §2-3 |
| 7 | 测试 surface 设计列出新增 multi-backend 用例清单（不实施） | ✅ | §7.3 + SA-E §5-6 (22 用例) |
| 8 | 所有产物均落入 design phase deliverables（research report 或 draft 文档），与真相层隔离 | ✅ | 本报告 status: draft；7 SA 草案落入 `.aw/worktrack/research-deliverables/`；真相层文档未触碰 |

### 9.2 boundary 自检

- ✅ 不修改 `aw-installer.js`
- ✅ 不修改 `path_safety_policy.json`
- ✅ 不修改 `distribution-entrypoint-contract.md` / `deploy-mapping-spec.md` / `goal-charter.md`
- ✅ 不修改 charter
- ✅ 不变更 release channel / dist-tag
- ✅ 不动 retained 分支 `feature-remove-python-deploy-code`
- ✅ 不实施任何测试代码
- ✅ 不开启 implementation-phase worktrack

---

## 10. 引用与下游

### 10.1 SubAgent 草案落点

| ID | 文件 | 行数 | 主题 |
|---|---|---|---|
| SA-A | `.aw/worktrack/research-deliverables/sa-a-command-protocol-decision.md` | 282 | 命令面 protocol 决议 |
| SA-B | `.aw/worktrack/research-deliverables/sa-b-transaction-semantics.md` | 380 | 多 backend 事务语义 |
| SA-C | `.aw/worktrack/research-deliverables/sa-c-trust-boundary.md` | 329 | 双根 trust boundary |
| SA-D D-1 | `.aw/worktrack/research-deliverables/sa-d-distribution-entrypoint-contract-revision.md` | 486 | distribution-entrypoint-contract 修订草案 |
| SA-D D-2 | `.aw/worktrack/research-deliverables/sa-d-deploy-mapping-spec-revision.md` | 453 | deploy-mapping-spec 修订草案 |
| SA-D D-3 | `.aw/worktrack/research-deliverables/sa-d-charter-tension-declaration.md` | 209 | Charter 张力声明 |
| SA-E | `.aw/worktrack/research-deliverables/sa-e-tui-cli-mapping-and-test-surface.md` | 525 | TUI/CLI 双面映射 + 测试 surface |

### 10.2 Worktrack 元数据

- `worktrack_id`: WT-20260507-aggregate-backend-design
- `branch`: wt-aggregate-backend-design
- `baseline_ref`: develop-aw@be787c7
- `node_type`: research
- `gate_criteria`: review-only
- `target_closeout_branch`: develop-aw（design phase 收口；implementation phase 需新一轮批准）

### 10.3 下游路径

- **design Gate**：本报告 + 7 SA 草案为 review evidence；validation 命令运行 folder_logic_check / path_governance_check / governance_semantic_check
- **implementation phase**：design Gate 通过后等待 programmer 新一轮批准；启动条件包括 truth-layer 写入授权 + aw-installer.js 实现授权
- **handback 时控制态字段更新**：design phase Gate 通过后 `.aw/control-state.md` 标记 design 收口、等待 implementation phase 批准
