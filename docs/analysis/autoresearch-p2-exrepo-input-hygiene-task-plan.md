---
title: "Autoresearch P2：Exrepo 输入卫生与连续 Loop 稳定化任务清单"
status: superseded
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch P2：Exrepo 输入卫生与连续 Loop 稳定化任务清单

> 说明：本文保留为上一版 exrepo 输入卫生施工记录叶子页，不是当前默认入口。
>
> 当前 `analysis/` 层分流入口请先回到 [Analysis README](./README.md)。
>
> 当前执行入口已切换为：
> [autoresearch-p2-tmp-exrepo-runtime-task-plan.md](./autoresearch-p2-tmp-exrepo-runtime-task-plan.md)
>
> 新规划已把目标收敛为：
>
> - 保留现有 `worktree` 生命周期
> - 将 exrepo 运行时迁到 OS 级 `/tmp`
> - 使用绝对路径重写后的 materialized suite 驱动 `baseline / round / replay`
> - 单独补齐 `/tmp` exrepo 维护脚本

## 一、规划目标

本任务清单只解决当前连续 loop 最主要的 3 个阻塞：

- baseline 之前缺少 exrepo routing-entry 健康检查
- prompt 入口仍然过度假设 repo-local skill 一定可用
- 修复后还缺少一次目标性 live 验证，无法确认 loop 是否真正恢复健康

本规划不覆盖：

- 多 prompt 联调
- Prompt 之外的参数搜索
- scheduler / selector 大改
- feedback ledger 重新设计
- 复杂跨 run study state

## 二、约束前提

本规划继续遵守当前 P2 收窄边界：

- 只优化单个 prompt 文件
- 只允许修改 Prompt 文本与最小必要 runner guard
- `backend` 固定为 `codex`
- `judge_backend` 固定为 `codex`
- 不把问题扩成新的研究平台

## 三、任务清单

### 任务ID：T-EXR-001
任务名称：为 exrepo baseline 增加 routing-entry preflight 与 capability report
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 在 baseline 真正调用 Codex 前，对 suite 中每个 exrepo 做一次 routing-entry 健康检查，并输出明确状态。
- 结果必须能把“输入面不可用”与“Prompt 表现差”分开，避免再次通过 300s timeout 才发现 wrapper 无效。

#### 2. 非目标（Non-goals）

- 不修改 mutation selector 逻辑
- 不重做 run-summary schema
- 不改变 baseline 的 fail-closed 总体策略
- 不引入新的 backend 或新的 stop policy

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/run_skill_suite.py`
  - 如有必要，新增 `toolchain/scripts/research/` 下的小型 helper
  - 相关测试文件
- Out-of-scope：
  - `product/`
  - `docs/knowledge/`
  - `.agents/`、`.claude/`、`.opencode/` 源码生成逻辑
  - mutation family 设计本身

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/run_autoresearch.py`
  - `toolchain/scripts/research/run_skill_suite.py`
  - `toolchain/scripts/research/backends/codex.py`
  - `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
  - `.autoworkflow/autoresearch/manual-cr-exrepos-codex-loop-r000002-m020070/baseline/train/20260329T032857Z-train/run-summary.json`
  - `.autoworkflow/autoresearch/manual-cr-exrepos-codex-loop-r000002-m020070/baseline/train/20260329T032857Z-train/01.typer.context-routing.skill.codex.raw.stderr.txt`
  - `.autoworkflow/manual-runs/context-routing-exrepos-codex-first-pass/train.yaml`
- 可选参考文件：
  - `.exrepos/*/.agents/skills/context-routing-skill/SKILL.md`
  - `.exrepos/*/.claude/skills/context-routing-skill/SKILL.md`
  - `docs/operations/autoresearch-minimal-loop.md`
- 不需要读取的区域：
  - `product/`
  - `docs/reference/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：先加一个轻量 preflight，再把结果写成 capability report 或明确错误分类。
- 检查至少覆盖：
  - repo 是否存在 `.agents/skills/context-routing-skill/SKILL.md`
  - 若存在，该 wrapper 引用的 canonical path 是否能在目标 repo 内解析
- 建议输出的最小状态：
  - `usable_repo_skill`
  - `missing_repo_skill`
  - `invalid_repo_skill_wrapper`
- baseline 在发现 invalid/missing 且没有明确 fallback 语义时，应 fail fast，并把具体 repo 列出来。

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：high
- 原因：跨 `runner + baseline + exrepo wrapper` 多处边界，风险在于把 blocked-before-baseline 与普通 skill timeout 混淆

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：无
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 1

#### 8. 风险与不确定性（Risks）

- 如果 preflight 过于宽松，仍会把无效 wrapper 放进 live run
- 如果 preflight 过于激进，可能误挡本来可 fallback 的 repo
- 若状态输出不明确，后续还是无法区分 blocked 与 score regression

#### 9. 验证计划（Validation Plan）

- Static：
  - 运行相关 Python 测试文件
- Test：
  - 覆盖 `usable_repo_skill / missing_repo_skill / invalid_repo_skill_wrapper`
  - 覆盖 baseline 在 invalid wrapper 时的 fail-fast 错误文本
- Runtime：
  - 可做单 repo preflight smoke，不要求立即跑完整 loop
- 是否可以做 smoke test：
  - 可以，建议先做 deterministic preflight smoke

#### 10. 完成标准（Exit Criteria）

- baseline 前已存在 exrepo routing-entry preflight
- 至少能明确区分 `usable_repo_skill / missing_repo_skill / invalid_repo_skill_wrapper`
- invalid wrapper 不再通过 live timeout 才暴露
- 相关测试通过

#### 11. 失败协议（Failure Handling）

- 若必须修改 exrepo 内容本身才能实现 preflight，必须先停止并报告
- 若无法在当前 runner 边界内表达 capability report，必须先报告最小新增文件/接口
- 若实现需要扩大到 selector 或 feedback ledger 重构，必须停止并收窄范围

### 任务ID：T-EXR-002
任务名称：把 context-routing research prompt 改成条件式 repo-skill 入口
任务类型（Task Type）：Implement

#### 1. 任务目标（Goal）

- 让当前研究 prompt 不再绝对要求“先走 repo-local skill”，而是只在 repo-local skill 可解析时使用它，否则直接基于目标 repo 真实结构做最小 routing。
- 结果必须降低 exrepo 中 skill 缺失或 wrapper 无效时的误导性读取路径。

#### 2. 非目标（Non-goals）

- 不改写 canonical skill wrapper 内容
- 不引入新的 task prompt 文件
- 不改 backend mount 机制
- 不做多 prompt 联动调整

#### 3. 任务边界（Scope）

- In-scope：
  - `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
  - 如有必要，相关最小测试或 smoke fixture
- Out-of-scope：
  - `.exrepos/` 内的 skill wrapper 文件
  - `product/`
  - 其他 3 个 research prompt

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
  - `toolchain/scripts/research/backends/codex.py`
  - `.exrepos/typer/.agents/skills/context-routing-skill/SKILL.md`
  - `.autoworkflow/autoresearch/manual-cr-exrepos-codex-loop-r000002-m020070/baseline/train/20260329T032857Z-train/01.typer.context-routing.skill.codex.prompt.txt`
  - `.autoworkflow/autoresearch/manual-cr-exrepos-codex-loop-r000002-m020070/baseline/train/20260329T032857Z-train/01.typer.context-routing.skill.codex.raw.stderr.txt`
- 可选参考文件：
  - `.exrepos/fmt/.agents/skills/context-routing-skill/SKILL.md`
  - `.exrepos/zustand/.agents/skills/context-routing-skill/SKILL.md`
- 不需要读取的区域：
  - `docs/knowledge/`
  - 其他 task prompt

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：局部 prompt 文本修改
- 建议语义：
  - 若 `.agents/skills/context-routing-skill/SKILL.md` 存在，且其要求的入口能在当前 repo 中解析，则优先使用它
  - 否则不要继续追踪该 wrapper，直接基于当前 repo 真实结构做最小 routing
- 保持原有 Route Card contract、最小依赖链、exact repo-relative path 这些已验证有效信号不变

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：单文件文本调整，但需要保持已有 winning signal，不要误伤当前有效约束

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-EXR-001
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 1

#### 8. 风险与不确定性（Risks）

- 条件入口写得太模糊，会让模型重新扩散阅读范围
- 条件入口写得太硬，可能在实际可用 wrapper 上失去 repo-local guidance
- 容易误伤已经被证明有效的 Route Card 固定 contract

#### 9. 验证计划（Validation Plan）

- Static：
  - 文本 diff 审查
- Test：
  - 如有 prompt fixture / smoke，可补最小断言
- Runtime：
  - 通过后续单 repo live smoke 验证 prompt 是否不再卡死在无效 canonical path
- 是否可以做 smoke test：
  - 可以，但建议与 T-EXR-003 合并执行

#### 10. 完成标准（Exit Criteria）

- prompt 不再绝对要求“先走 repo-local skill”
- prompt 明确表达 repo-local skill 仅在可解析时使用
- 现有 Route Card contract 与已验证有效信号保持不变

#### 11. 失败协议（Failure Handling）

- 若必须同步修改 exrepo wrapper 才能让 prompt 合理，必须停止并回报依赖外部输入面改动
- 若 prompt 改动无法同时保留当前 winning contract，必须先回报冲突点
- 不允许顺手扩展到其他 task prompt

### 任务ID：T-EXR-003
任务名称：执行一次目标性 live 验证并记录修复后观察结论
任务类型（Task Type）：Review

#### 1. 任务目标（Goal）

- 在 T-EXR-001 和 T-EXR-002 完成后，用最小 live 验证确认：baseline 不再因为已知 routing-entry 问题卡死，且 continuous loop 至少能进入 round。
- 结果必须产出可复用的观测结论，而不是只给 exit code。

#### 2. 非目标（Non-goals）

- 不追求完整 acceptance matrix
- 不要求多轮大规模研究
- 不在本任务内继续改 scheduler / selector
- 不做大范围结果分析平台

#### 3. 任务边界（Scope）

- In-scope：
  - `.autoworkflow/manual-runs/context-routing-exrepos-codex-first-pass/`
  - `.autoworkflow/autoresearch/` 下新的本轮运行产物
  - 必要时更新 `docs/analysis/` 下的观测记录
- Out-of-scope：
  - `product/`
  - 其他无关 live 验证矩阵

#### 4. 输入上下文（Context）

- 必须阅读的文件：
  - `.autoworkflow/manual-runs/context-routing-exrepos-codex-first-pass/contract-loop.json`
  - `.autoworkflow/manual-runs/context-routing-exrepos-codex-first-pass/registry-seed.json`
  - `docs/operations/autoresearch-minimal-loop.md`
  - `docs/analysis/autoresearch-p2-lightweight-single-prompt-codex-loop.md`
- 可选参考文件：
  - 最新 baseline / round / decision 产物
- 不需要读取的区域：
  - `product/`

#### 5. 执行策略（Execution Strategy）

- 推荐执行方式：
  - 先做一个代表性 repo 的 live smoke，验证 prompt 不再卡在无效 wrapper
  - 再做一轮 continuous loop 试跑
- 观测重点：
  - baseline 是否完成
  - 是否进入 `prepare-round`
  - 是否进入 `run-round`
  - stop 原因是什么
  - 是否还有 repo 因 `missing_repo_skill / invalid_repo_skill_wrapper` 被前置拦截

#### 6. 模型与推理建议（Execution Profile）

- 推荐模型：CodeX
- 推理等级：medium
- 原因：主要是执行与观测收口，不是复杂实现

#### 7. 依赖关系（Dependencies）

- 前置任务（必须完成）：T-EXR-001、T-EXR-002
- 可并行任务：无
- 是否属于某个批次（Batch）：Batch 2

#### 8. 风险与不确定性（Risks）

- live backend 结果仍可能受网络、服务波动、模型侧行为影响
- 即使旧阻塞被去掉，也可能暴露新的 repo-specific 问题
- 如果只看 exit code，不看产物，会再次丢掉可解释信号

#### 9. 验证计划（Validation Plan）

- Static：
  - 无
- Test：
  - 至少保留 deterministic 单测全绿
- Runtime：
  - 1 次代表性 live smoke
  - 1 次 continuous loop 试跑
- 是否可以做 smoke test：
  - 本任务本身就是 smoke + loop validation

#### 10. 完成标准（Exit Criteria）

- 有一轮 live 验证结果
- 能明确回答：
  - baseline 是否完成
  - loop 是否进入 round
  - 当前新的首要阻塞是什么
- 结果已回写为可复用观察结论

#### 11. 失败协议（Failure Handling）

- 若仍在 baseline 前失败，必须输出具体 repo 和状态分类
- 若 live backend 不可用，必须记录环境阻塞而不是误判为 prompt 回退
- 若暴露的是新输入面问题，不得在本任务内继续扩边修复

## 四、任务依赖图

- T-EXR-001 是起点任务，先把 exrepo 输入面 health gate 立起来。
- T-EXR-002 依赖 T-EXR-001，因为 prompt 的条件式入口应与 preflight 输出的可用性语义一致。
- T-EXR-003 依赖 T-EXR-001 和 T-EXR-002，因为必须在 gate 和 prompt 都收紧后，live 验证才有意义。

## 五、推荐执行顺序（Batch 划分）

### Batch 1

- T-EXR-001：实现 exrepo routing-entry preflight 与 capability report
- T-EXR-002：把 context-routing research prompt 改成条件式 repo-skill 入口

### Batch 2

- T-EXR-003：执行目标性 live smoke 和 continuous loop 试跑，并记录观察结论

## 六、可并行执行的任务组

- 当前不建议并行执行核心实现任务。
- T-EXR-002 依赖 T-EXR-001 的状态语义，若并行容易导致 prompt wording 与 preflight 输出分类不一致。
- 可接受的并行方式只有：在 T-EXR-001 接近完成时，由另一 Agent 预读 T-EXR-002 上下文，但不得先提交实现。

## 七、高风险任务列表

- T-EXR-001
  - 风险最高，因为它定义了“blocked-before-baseline”的前置卫生条件，若做错会误挡 valid repo 或放过 invalid wrapper。
- T-EXR-003
  - 有 live backend 波动风险，但这是验证面风险，不是架构复杂度风险。

## 八、推荐整体执行策略

- 先把“能不能安全开始 baseline”变成显式 gate，再谈 continuous loop 的 stop/continue。
- 先修输入面，再修迭代行为；不要在 exrepo 输入卫生条件未稳定前继续堆 mutation family。
- 把 live 验证放在最后，只做一次目标性确认，不要提前扩成大规模 acceptance matrix。
