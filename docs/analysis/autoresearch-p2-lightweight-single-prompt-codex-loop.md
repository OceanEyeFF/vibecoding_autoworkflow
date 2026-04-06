---
title: "Autoresearch P2：单 Prompt、Codex-only 轻量迭代方案"
status: active
updated: 2026-04-06
owner: aw-kernel
last_verified: 2026-04-06
---
# Autoresearch P2：单 Prompt、Codex-only 轻量迭代方案

> 目的：在不把 `autoresearch` 扩成独立大系统的前提下，为当前仓库补一条低侵入、低变量、可回放的 Prompt 文本微调闭环。本文只固定一版最小设计草案，不直接替代 `docs/operations/` 的现行 runbook，也不直接替代 `toolchain/` 的当前实现合同。

## 当前承接状态

截至 `2026-03-28`，本文中的 Batch 1 到 Batch 3 最小落地边界已经承接到：

- `docs/operations/autoresearch-minimal-loop.md`
- `toolchain/scripts/research/README.md`

本文继续保留为：

- P2 方案为什么最初要收窄为“单 Prompt、默认 `codex -> codex`、低变量”的设计记录
- 尚未升格为主线运行说明的背景约束与取舍说明

因此，如果当前任务是“实际发起或复核已实现的 P2 run”，应优先读取上面的 runbook 和脚本入口文档，而不是把本文当作唯一执行入口。

## 一、定位

这份草案只解决一个问题：

- 如何对单个 task prompt 做多轮文本微调，并由 `Codex` 完成执行与评测

它不解决：

- 多 prompt 联调
- Prompt 之外的参数搜索
- 多 backend 对照实验
- 跨 run 的长期研究数据库
- 自动 proposal engine

因此它不是新的通用优化平台，而是当前 `autoresearch` 轨道上的一个轻量收窄方案。

## 二、设计约束

本方案固定采用下面约束：

- 一次 run 只优化一个 prompt 文件
- 一次 run 只对应一个 task
- 只允许修改 Prompt 文本本身
- `backend` 固定为 `codex`
- `judge_backend` 固定为 `codex`
- 不同时修改 canonical skill、adapter wrapper、docs 规则正文

这组约束的目标不是“功能最全”，而是：

- 降低变量面
- 降低实现侵入程度
- 让 round 结果更容易解释
- 避免把当前项目拖进重型研究系统

## 三、当前可优化对象

当前 runner 里实际消费的 task prompt 有 4 个：

- `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
- `toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md`
- `toolchain/scripts/research/tasks/task-contract-skill-prompt.md`
- `toolchain/scripts/research/tasks/writeback-cleanup-skill-prompt.md`

本方案要求：

- 每次 run 只能从这 4 个文件里选 1 个
- 该 run 内所有 mutation 都只能落在这 1 个文件上

## 四、最小对象模型

建议在现有 contract 基础上增加两项轻量约束字段：

- `target_task`
- `target_prompt_path`

建议语义：

- `target_task`：本次 run 唯一允许执行的 task
- `target_prompt_path`：本次 run 唯一允许修改的 prompt 文件

配套强校验：

- suite 只能覆盖 `target_task`
- `mutable_paths` 只能包含 `target_prompt_path`
- 默认 backend pair 仍假定 `codex -> codex`；当前已实现代码允许 contract 用 `expected_backend / expected_judge_backend` 显式覆盖这对默认值

说明：

- 这里优先采用“收窄约束 + 运行时强校验”
- 不要求一开始重做完整 schema 设计
- 若后续证明稳定，再决定是否升格为正式 schema 字段

## 五、约束真相层定案

为避免 `T-001` 和 `T-002` 各自发明一套边界语义，本方案先固定一版实现前定案：

- P2 约束真相层由共享 P2 preflight 提供，CLI 入口和 replay 路径都必须复用同一套校验
- contract 只承载两项轻量真相字段：
  - `target_task`
  - `target_prompt_path`
- 默认 `codex -> codex` 不作为 contract 主 schema 的静态真相，而是在 P2 preflight 中解析 suite manifest 后做强校验；当前实现已允许 contract 声明期望 backend pair 覆盖默认值
- 通用 `load_contract()` 继续承担通用合同校验，不直接变成 P2 专属 fail-closed 入口
- P2 专属收紧只在显式 P2 路径上生效，避免误伤当前已存在的非 P2 fixture 和 smoke

采用这版定案的原因是：

- 能把 `T-001` 的责任收敛到“定义并冻结边界”
- 能把 `T-002` 的责任收敛到“执行同一套边界”
- 能避免 contract、CLI、registry、round 各自维护不同的单 prompt 语义

### Task / Prompt 固定映射

为减少 `T-002` 返工，本方案同时固定 `target_task` 和 `target_prompt_path` 的一一映射：

- `context-routing-skill` -> `toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
- `knowledge-base-skill` -> `toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md`
- `task-contract-skill` -> `toolchain/scripts/research/tasks/task-contract-skill-prompt.md`
- `writeback-cleanup-skill` -> `toolchain/scripts/research/tasks/writeback-cleanup-skill-prompt.md`

P2 preflight 需要同时校验：

- `target_prompt_path` 必须命中上面的 4 个 prompt 文件之一
- `target_task` 必须与 `target_prompt_path` 的映射一致
- `mutable_paths` 在 P2 模式下必须规范化为只包含 `target_prompt_path`

## 六、Mutation 边界

本方案不需要新的复杂 scheduler，只需要收紧 mutation discipline。

一次 round 的 mutation 建议只允许：

- `text_rephrase`
- `example_trim`
- `instruction_reorder`

当前阶段不建议允许：

- 多文件联动修改
- Prompt 外参数调整
- skill wrapper 和 task prompt 同时改写
- 文档规则与 prompt 同轮共改

配套 guardrail：

- `target_paths` 必须只指向 `target_prompt_path`
- diff 应尽量保持局部
- 同一 round 不允许跨到其他 prompt 文件
- registry 和 round 都只允许消费 `target_prompt_path` 这一单一来源，不得自行推导第二套 prompt 目标语义

## 七、Codex-only 执行面

本方案把 `Codex` 定为唯一执行与评测后端。

设计默认口径：

- worker backend = `codex`
- judge backend = `codex`

原因：

- 当前目标是优化 `Codex` 软件环境中的 Prompt
- 如果执行端和评测端分离到不同 backend，会引入额外行为偏差
- 在单 Prompt 微调场景下，`codex -> codex` 的解释成本最低

因此这里不再把 `claude -> codex` 作为默认研究主路径，只保留它在其他研究场景中的价值。

## 八、最小停机规则

当前只有 `max_rounds` 还不够，但也没有必要引入复杂 stop policy。

建议固定 3 条轻量规则：

### 1. 连续无提升停机

- 连续 3 轮没有产生新的 validation champion，则停止

### 2. 候选耗尽停机

- 所有 active mutation family 都至少尝试过 1 次，且没有任何 `keep`，则停止

### 3. 新冠军复评

- 任一 round 命中 `keep` 后，立即用同一配置 replay 1 次
- replay 必须先复用同一套 P2 preflight，不能绕开单 prompt 与 contract 期望 backend pair 约束；未声明时默认仍是 `codex -> codex`
- 若 replay 不能保持 validation 相对本轮 round validation 不下降，则该 round 视为不稳定，不升级 champion
- replay 复跑前应先清空旧的 `replay/` 子目录，避免陈旧产物污染结果

这 3 条规则的目的分别是：

- 防止机械空转
- 防止把“全试过但都没用”的 run 无限拖长
- 防止单次偶然得分把噪声误判为改进

## 九、建议保留与建议避免

### 建议保留

- 现有 `init -> baseline -> prepare-round -> run-round -> decide-round` 闭环
- 现有 mutation registry / worker contract / feedback ledger 结构
- 现有固定 keep / discard 规则
- 现有 candidate/champion worktree 隔离模型

### 建议避免

- 新增 proposal engine
- 新增跨 run study memory
- 同时优化多个 prompt
- 让模型自由决定 stop 条件
- 在当前阶段扩成通用参数搜索器

## 十、最小施工清单

如果采用本方案，建议只做下面几件事：

1. 在 `run_autoresearch.py` 中增加 `single-prompt codex-only` 运行前校验。
2. 在 `autoresearch_mutation_registry.py` 中增加“单 prompt target”约束。
3. 在 `autoresearch_round.py` 或 `run_autoresearch.py` 中增加轻量 stop rule。
4. 为 `codex -> codex` 的单 prompt 路径补一条最小 smoke。
5. 在 `docs/operations/` 中补一页对应 runbook，前提是实现已经落地并验证通过。

## 十一、与现有文档体系的关系

本文当前属于：

- `analysis/` 下的轻量设计草案
- 研究轨道的后续收窄方案

它当前不是：

- `docs/knowledge/` 中的主线规则
- `docs/operations/` 中的已验证运行说明
- `toolchain/` 中已落地实现的正式合同

如果后续接受并落地本文结论，应优先回写到：

- `toolchain/scripts/research/README.md`
- `docs/operations/autoresearch-minimal-loop.md`

如有必要，再进一步升格到：

- `docs/knowledge/`

## 十二、一句话结论

当前最值得做的，不是把 `autoresearch` 扩成更大的系统，而是把它压缩成：

- 单 task
- 单 prompt
- `codex -> codex`
- 有最小停机规则

这版边界更适合当前仓库的投入强度，也更容易得到可解释的 Prompt 微调结果。

## 十三、2026-03-29 exrepos integration 试跑观察

本轮在 integration worktree 上做了两次 live 验证：

- 代表性 smoke：
  - 命令：`python3 toolchain/scripts/research/run_skill_suite.py --repo /mnt/e/repos/wsl/personal/vibecoding_autoworkflow/.exrepos/typer --backend codex --task context-routing --with-eval --save-dir .autoworkflow/t-exr-003/smoke-typer`
  - 结果：`typer` 成功完成 skill + eval，最终 `12/12`
  - 产物：`.autoworkflow/t-exr-003/smoke-typer/20260329T052552Z-typer/`
- continuous loop：
  - contract：`.autoworkflow/manual-runs/context-routing-exrepos-codex-first-pass/contract-loop.json`
  - run id：`manual-cr-exrepos-codex-loop-r000001-m020069`
  - 产物：`.autoworkflow/autoresearch/manual-cr-exrepos-codex-loop-r000001-m020069/`

### 直接结论

- 旧的 `typer` routing-entry 路径假设问题没有复现；当前 prompt 在 `typer` 上能跳过无效 repo-local skill wrapper，并直接从 repo 证据完成 Route Card。
- continuous loop 没有进入 `prepare-round` / `run-round`；它卡在 baseline validation，而不是卡在旧的 baseline train `typer` timeout。
- 当前新的首要阻塞是 `vite-plus`：
  - validation suite 中 `vite-plus` 的 skill phase `300s` 超时
  - 最终 `03.vite-plus.context-routing.skill.codex.final.txt` 为空
  - eval 因空输出被打成 `4/12`
  - 整条 `validation.yaml` 因 suite failed 终止，baseline 未完成，所以没有 `scoreboard.json`，`history.tsv` 也没有 baseline 行

### 重要附加发现

- 当前 integration worktree 的 exrepo routing-entry preflight 没有真正覆盖这次 loop：
  - 运行产物里没有生成 `routing-entry-capability.json`
  - 代码上，`collect_context_routing_suite_repo_skill_report()` 只会收集位于 `REPO_ROOT/.exrepos` 下的 repo
  - 这次 suite 使用的是主工作区的绝对路径 `.exrepos/*`
  - 当 runner 从 integration worktree 执行时，这些绝对路径不在 integration worktree 的 `REPO_ROOT/.exrepos` 下，因此 capability report 为空，preflight 被静默跳过

### 当前可复用判断

- `T-EXR-001` 和 `T-EXR-002` 已经足够证明：旧的 repo-local wrapper 误导问题可以被 prompt + baseline guard 缓解。
- `T-EXR-003` 的 live 结果说明：continuous loop 目前仍未健康启动，但新的主阻塞已经从 `typer` wrapper 冲突转移到：
  - `vite-plus` 这类大 repo 的 routing timeout
  - integration worktree 下绝对 exrepo 路径未被 preflight 纳入
- 这轮任务到此应停止记录，不在本任务内继续扩边修复。

## 十四、2026-03-29 core-only gating rerun

随后做了两项最小收窄：

- baseline / round / replay 统一把 `contract.timeout_policy.seconds` 下传到 `run_skill_suite.py`
- continuous loop 的 gating split 改成：
  - `train`: `typer`, `zustand`, `trackers`, `russh`
  - `validation`: `fmt`
  - `acceptance`: `JUCE`, `vite-plus`

基于这版配置重新运行 continuous loop：

- run id：`manual-cr-exrepos-codex-loop-r000002-m020070`
- 产物：`.autoworkflow/autoresearch/manual-cr-exrepos-codex-loop-r000002-m020070/`

结果：

- baseline 完成
- loop 进入 round，并连续完成 3 轮
- stop 原因：`3 consecutive completed rounds without a new validation champion`

关键分数：

- baseline: train `11.5`, validation `12.0`
- round 1: discard, train `11.75`, validation `11.0`
- round 2: keep, train `11.75`, validation `12.0`
- round 3: discard, train `11.75`, validation `12.0`

本轮 winning mutation：

- `text_rephrase:context-routing-skill:minimal-trace-and-direct-paths-v1#a001`

这次 rerun 的意义很直接：

- continuous loop 现在已经能在当前仓库里稳定启动并进入 round
- 对当前阶段而言，把 heavyweight repo 从 gating loop 拿掉，比继续单纯放大 timeout 更有效
- `timeout_policy` 的真实下传仍然值得保留，因为它修复了 contract 和实际 runner 行为不一致的问题
