---
title: "Autoresearch P1.Final：Agent Teams 讨论结果 v3"
status: active
updated: 2026-03-27
owner: aw-kernel
last_verified: 2026-03-27
---

> 说明：本文档是 Agent Teams 代码审计讨论的结果，基于代码事实对齐后的务实分析。
> 原始风险登记见 `autoresearch-p1-final-risk-register-and-followups.md`。
> 本文档聚焦于"先让循环跑起来"的务实目标，不替代原始风险登记。

## 一、背景与目标

### 项目现状
- P1.1-P1.3 代码已实现，但**从未端到端跑过**
- 目标第一优先级：**服务好循环可以运行**
- 目标第二优先级：**循环迭代中 Skill/Agents 文档能稳定变好**

### Agent Teams 讨论原则
- 所有结论必须基于代码审计（直接引用行号）
- 不基于二手结论猜测
- 区分"阻塞问题"和"完整性退化风险"

## 二、代码审计确认的事实

### 1. Legacy Worker-Contract 实际行为

**代码位置**：`autoresearch_round.py:602-630`

| 维度 | v1 (Legacy) | v2 |
|------|-------------|-----|
| **触发条件** | 缺少 `worker_contract_sha256` | 有 `worker_contract_sha256` |
| **SHA256 校验** | ❌ 无 | ✅ 有 |
| **Payload 重建对比** | ❌ 无 | ✅ 有 |
| **Agent 上下文** | ❌ 无（只有 7+1 tracing 字段） | ✅ 有 |
| **一致性校验函数** | `validate_legacy_worker_contract_consistency` | `validate_worker_contract_consistency` |

**v1 Legacy 分支校验的 7+1 个字段**（`autoresearch_worker_contract.py:231-248`）：
1. `round` - 轮次编号
2. `mutation_key` - 突变键
3. `fingerprint` - 突变指纹
4. `mutation_sha256` - 突变内容 SHA256
5. `candidate_worktree` - 候选工作树路径
6. `candidate_branch` - 候选分支名
7. `base_sha` - 基准 commit SHA
8. `candidate_worktree` 与 `worktree_payload["path"]` 匹配

**结论**：✅ Legacy 分支**不是阻塞问题**，是**完整性退化风险**。系统可以正常运行，只是 agent-facing 字段（instruction, target_paths, guardrails, expected_effect）校验能力明显弱于 v2。

---

### 2. Registry 写回真实时序

**代码位置**：`run_autoresearch.py:338-358`

```python
# 第 338 行 - 步骤1
round_manager.stage_mutation(contract.run_id, round_number, mutation_payload)

# 第 340-345 行 - 步骤2
worker_contract_path = round_manager.stage_worker_contract(...)

# 第 348-352 行 - 步骤3: Registry 写回
entry["attempts"] = attempt
entry["last_selected_round"] = round_number
write_mutation_registry(registry_path, registry_payload)

# 第 353-358 行 - 步骤4: Round Authority 快照
round_manager.stage_round_authority(...)
```

**关键结论**：
- ❌ `stage_worker_contract()` 失败**不会**提前写脏 registry（registry 写回在其之后）
- ⚠️ **真正的残留风险窗口**：第 352 行之后、第 358 行之前
  - 即 `write_mutation_registry()` 成功后、`stage_round_authority()` 执行前的进程 crash
  - 会导致 Registry 记录了 round 已 prepare，但 Authority 快照未完成

---

### 3. Feedback Ledger 实际行为

**代码位置**：
- `autoresearch_feedback_distill.py:120-123` — 缺文件返回 `[]`
- `autoresearch_selector.py:92` — `adaptive_mode = bool(feedback_ledger)`

```python
def load_feedback_ledger(path: Path) -> list[dict[str, Any]]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        return []  # 静默返回空列表
```

| 场景 | `load_feedback_ledger()` | adaptive_mode | selection_reason |
|------|-------------------------|---------------|------------------|
| ledger 文件不存在 | `[]` | `False` | `"lowest_attempt_count"` |
| ledger 空文件 | `[]` | `False` | `"lowest_attempt_count"` |
| ledger 有内容 | `[{...}, ...]` | `True` | `"adaptive_priority"` |

**结论**：✅ 是 **observability 问题**，不是 correctness 阻塞。第一轮运行时退化为 deterministic 是预期行为，但需要加日志让用户知道当前模式。

---

## 三、真正的阻塞点分析

### 阻塞问题清单

| 阻塞问题 | 根因 | 代码位置 |
|---------|------|---------|
| **Registry 与 Authority 时序** | `write_mutation_registry` 成功后、`stage_round_authority` 执行前的 crash | `run_autoresearch.py:352-358` |
| **空 diff guardrail** | candidate worktree 没有实际 mutation 时会失败 | `autoresearch_round.py:425-426` |
| **Suite 文件路径解析** | candidate worktree 未正确创建时 fallback 可能失败 | `autoresearch_round.py:783-792` |

### 详细分析

#### 1. Registry 与 Authority 时序

`run-round` 的 `_load_authoritative_mutation`（`autoresearch_round.py:447-454`）依赖 `last_selected_round` 匹配：

```python
selected_entries = [
    entry for entry in registry.entries
    if int(entry.get("last_selected_round") or 0) == round_number
]
if len(selected_entries) != 1:
    raise RuntimeError(
        "Mutation registry must contain exactly one entry selected for the active round."
    )
```

**阻塞链**：
- 如果 `prepare-round` 在 Registry 写回后、`stage_round_authority` 完成前被中断
- 则 `run-round` 可能找不到正确的 entry

#### 2. 空 diff guardrail

`autoresearch_round.py:425-426`：

```python
if require_non_empty_diff and not touched_paths:
    raise RuntimeError("Candidate diff must be non-empty when require_non_empty_diff is enabled.")
```

**阻塞链**：第一次跑烟测时，如果用户没有实际做 mutation，round 会因为空 diff 而失败。

#### 3. Suite 文件路径解析

`autoresearch_round.py:783-792` 的 `_resolve_candidate_suite`：

```python
def _resolve_candidate_suite(self, candidate_worktree: Path, suite_file: Path) -> Path:
    resolved_suite = suite_file.expanduser().resolve()
    try:
        relative = resolved_suite.relative_to(self.repo_root)
    except ValueError:
        return resolved_suite
    candidate_suite = (candidate_worktree / relative).resolve()
    if candidate_suite.is_file():
        return candidate_suite
    return resolved_suite  # fallback 到 repo_root
```

**问题**：如果 candidate worktree 未正确创建，fallback 可能导致 suite 执行失败。

---

## 四、Skill/Agents 文档稳定性评估

### 当前文档循环的结构

```
循环输入侧（告诉 agent 做什么）
├── product/memory-side/skills/*/SKILL.md      ← 能力封装定义
├── docs/knowledge/memory-side/skills/*.md      ← skill skeleton（知识合同层）
└── product/*/adapters/*/skills/*/SKILL.md    ← 后端适配层

循环输出侧（记录 agent 学到了什么）
├── docs/knowledge/*/                           ← 回写的项目真相
├── docs/analysis/*                            ← 研究记录
└── docs/ideas/*                               ← 新想法（待评估）
```

### 文档改进循环断掉的最后一环

```
feedback-distill.suggested_adjustments → 没有机制 → 无法回写到 mutation-registry.instruction_seed
                                              → 无法回写到 SKILL.md
```

**当前状态**（`autoresearch_feedback_distill.py:218`）：
- `suggested_adjustments` 仍是空占位
- `dimension_feedback_summary` 仍是空占位
- 没有机制将"建议"转化为"新的 instruction_seed 候选"

### "文档稳定变好"的衡量指标

| 指标 | 当前是否可测 | 如何落地 |
|------|------------|---------|
| `parse_error_rate == 0` | ✅ 是 | 已有 |
| Route Card 正确率 ≥ 95% | ✅ 是 | skill-suite 中测 |
| `writeback_coverage >= 0.9` | ❌ 否 | 需新增 |
| 跨后端 SKILL.md diff 为空 | ✅ 是 | `diff` 检查 |
| instruction_seed 自我演进 | ❌ 否 | 需新增 P1.4 |

---

## 五、务实的行动清单

### 🔴 P0 - 让基本流程能跑

| 优先级 | 动作 | 原因 |
|--------|------|------|
| **P0** | **做一次真实手动端到端** | 验证 `init → baseline → prepare-round → run-round → decide-round` 完整链路 |
| **P0** | **确保 candidate worktree 有实际 mutation** | 第一次跑时要真的做 mutation，否则 `require_non_empty_diff` 会失败 |
| **P0** | **检查 suite 文件路径解析** | candidate worktree 正确创建 + suite fallback 到 repo_root |

### 🟠 P1 - 加日志（第一次烟测时就应加）

| 动作 | 目的 | 代码位置 |
|------|------|---------|
| `write_mutation_registry` 后加日志 | 知道 registry 写回完成 | `run_autoresearch.py:352` |
| `stage_round_authority` 后加日志 | 知道 authority 快照完成 | `run_autoresearch.py:358` |
| selector 中加 feedback ledger 降级日志 | 知道是 deterministic 还是 adaptive 模式 | `autoresearch_selector.py:92` |

### 🟡 P2 - 跑起来后验证

| 验证项 | 期望 |
|--------|------|
| `attempts` 计数是否正确 | 每次 prepare-round 后 +1 |
| `fingerprint` 冲突跳过是否正确 | duplicate 应该被 skip |
| scoreboard 分数与 keep/discard 结果对比 | 验证裁决逻辑 |
| `last_selected_round` 在多轮后是否正确推进 | multi-round 一致性 |

### 🟢 可以容忍（不影响核心循环）

| 问题 | 容忍理由 |
|------|----------|
| Legacy worker-contract 弱校验 | 只有旧数据才触发，当前走 v2 |
| Registry Bookkeeping 可手工改写 | 完整性风险，非功能阻塞 |
| 正信号 family 过度重复利用 | 多轮后才暴露 |
| `suggested_adjustments` / `spawn_proposal` 空占位 | P1.3 已确认，不影响核心循环 |
| `target_paths` overlap 校验 | P1.Final 已标记，第一轮不会触发 |

---

## 六、与原始风险登记的对比

| 原始风险登记结论 | Agent Teams 代码审计修正 |
|----------------|------------------------|
| Legacy worker-contract 是"烟测前唯一必须修" | ❌ 已修正：不是阻塞问题，是完整性退化风险 |
| Registry 在 stage_worker_contract() 失败前就被写脏 | ❌ 已修正：当前顺序是 stage_mutation → stage_worker_contract → write_registry |
| Feedback ledger 静默降级是 correctness 阻塞 | ⚠️ 已修正：是 observability 问题，不是 correctness 阻塞 |
| 文档稳定性闭环缺口 | ✅ 确认：suggested_adjustments 空占位，确实断在最后一环 |

---

## 七、后续需要确认的事项

1. **第一次端到端**：是否接受"先手动跑一次最小化的完整流程"作为第一步？

2. **日志优先级**：是否在第一次烟测前先加好 feedback ledger 降级日志？

3. **空 diff guardrail**：如果第一次跑时没有做实际 mutation，是否要临时关闭 `require_non_empty_diff`？

---

## 八、与文档体系的互链

- **本文档**：基于代码审计的务实分析，聚焦"先让循环跑起来"
- **原始风险登记**：[autoresearch-p1-final-risk-register-and-followups.md](./autoresearch-p1-final-risk-register-and-followups.md) — 完整的 P1.Final 风险登记，包含原始风险列表和后续建议 A-H
- **已承接的 repo-local runbook**：[../operations/autoresearch-minimal-loop.md](../operations/autoresearch-minimal-loop.md) — 已实际跑通的一轮最小闭环、执行顺序与产物位置
- **升格路径**：如研究结论被接受，需同步写入 `docs/knowledge/`、`docs/operations/` 或 `toolchain/` 入口说明
