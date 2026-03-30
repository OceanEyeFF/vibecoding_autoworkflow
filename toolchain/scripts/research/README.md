# Research Scripts

本目录放 research runner 脚本与 prompt 入口，不承载研究产物本身。

当前结构：

- `run_skill_suite.py`：统一 runner，支持 direct run 和 suite run
- `run_claude_skill_eval.py`：Claude 兼容壳，参数翻译后委托 `run_skill_suite.py`
- `run_backend_acceptance_matrix.py`：live acceptance 入口，固定跑 `codex -> codex` 与 `claude -> codex` 两条矩阵
- `run_autoresearch.py`：autoresearch P0.1/P0.2/P0.3/P1.1/P1.2/P1.3 入口，负责 baseline 数据面、suite materialization、worktree 控制壳、registry materialization、worker contract、feedback distillation 与 round 外环
- `refresh_manual_run_contract.py`：给手动单轮 contract 刷新一个 fresh `run_id`；使用单调 `serial` 加 `mod 100003` residue，避免复用旧 run 状态
- `manage_tmp_exrepos.py`：读取 `exrepo.txt` 里的 `owner/repo` 清单，把 bare repo name 对应的 tmp exrepo clone / pull 到稳定 `/tmp` 根；`git pull` 失败时会先 `git reset --hard` 再重试 `git pull`
- `autoresearch_contract.py`：P0.1 contract 读取、schema 校验、suite/path 边界校验
- `autoresearch_scoreboard.py`：P0.1 baseline scoreboard 聚合与校验
- `autoresearch_round.py`：P0.3 round 生命周期与 P1.2 的 mutation / worker-contract authority 校验、round scoreboard / decision 聚合
- `autoresearch_mutation_registry.py`：P1.1 mutation registry 的 schema 校验、contract 边界校验、canonicalize 与 fingerprint 计算
- `autoresearch_worker_contract.py`：P1.2 worker contract 的 schema 校验与生成（agent-facing envelope）
- `autoresearch_selector.py`：P1.2/P1.3 selector，保留 deterministic 基线，并在有 distilled ledger 时按 family signal 做 feedback-aware priority
- `autoresearch_feedback_distill.py`：P1.3 deterministic feedback distillation、ledger upsert 与 family signal helper
- `worktree_manager.py`：P0.2 的 git worktree 生命周期管理器
- `exrepo_runtime.py`：TMP exrepo 根目录解析与 suite 物化 helper；只重写运行时输入，不负责 clone / fetch / reset
- `exrepo.txt`：tmp exrepo 的 GitHub repo 清单，一行一个 `owner/repo`
- `backends/`：backend registry、抽象 contract、以及 `claude / codex / opencode` 适配层
- `common.py`：repo/task/suite/eval schema/artifact 的共享解析与写盘逻辑
- `tasks/`：skill research prompt 模板

## 运行模型

`run_skill_suite.py` 是主入口。

- `--repo` 模式：对单个 repo 执行一个 task 或全部 task
- `--suite` 模式：从 `toolchain/evals/fixtures/suites/` 或显式 manifest 路径加载一组 runs
- `--with-eval`：每个 skill run 后追加对应 eval run；judge backend 默认继承 `--backend`
- `--save-dir`：可选；runner 会在该目录下创建一个 `UTC 时间戳 + slug(label)` 的 run 子目录
- `--jobs`：可选；按 spec pipeline 并发执行。每条 pipeline 内仍保持 `skill -> eval` 顺序，默认 `1`
- `--timeout`：单个 phase 的 timeout，默认 `300` 秒；它约束的是一次 skill run 或一次 eval run，不是整条 live smoke 的总墙钟时间

live Codex smoke 的预算口径当前建议固定为：

- direct `single run`：至少沿用默认 `300s` phase budget，不要用 `120s` 这类紧预算作为健康门槛
- `run + eval` 或 suite live smoke：按 `skill + eval` 两段累计看待，单 repo lane 的总墙钟预算建议预留 `5` 到 `10` 分钟
- 如果想做更便宜的快速回归，优先跑 deterministic/unit tests；不要把过紧的 live backend timeout 当成脚本故障证据

兼容入口 `run_claude_skill_eval.py` 只保留 Claude 旧调用方式：

- 固定转发为 `--backend claude`
- `--with-eval` 时固定转发 `--judge-backend claude`
- 其余参数仍使用当前 unified runner 的执行与落盘逻辑

`run_backend_acceptance_matrix.py` 则是另一层定位：

- 它不是新的 runner，只是为 live acceptance 生成一份临时 suite，再委托 `run_skill_suite.py`
- 固定矩阵是 `codex -> codex` 与 `claude -> codex`
- 每条 lane 都跑 `task: all`，因此会覆盖四个 skills
- 这是高成本、真实 backend 的系统级验收，不是普通 deterministic regression

`run_autoresearch.py` 当前覆盖 P0 到 P1.3 的最小边界：

- `init`：读取并校验 contract，初始化 `.autoworkflow/autoresearch/<run-id>/contract.json` 与 `history.tsv`
- `baseline`：按 contract 分开执行 train/validation suite；保留原始 suite preflight，再把 suite 物化到 run-local artifact 后执行，写 `scoreboard.json`、记录 baseline 历史行，并把 `runtime.json` 的 `champion_sha` 同步到这次 baseline 实际评测的 HEAD
- baseline 只跑 train/validation；acceptance suite 仅作为 contract fixture 引用，不在 P0.1 默认 baseline 中执行
- `prepare-round`：在不切换当前工作树的前提下创建 `candidate/<run-id>/rNNN` 和独立 worktree，并写 `runtime.json`、`round.json`、`worktree.json`
- `prepare-round` 默认会从 run-local `mutation-registry.json` 自动选择下一条可用 entry；当前 selector 输入包含 registry、runtime、比较基线 scoreboard，以及可选的 `feedback-ledger.jsonl`，在没有 ledger 时保持 P1.2 的 deterministic 规则，有 ledger 时则按 family signal 做 feedback-aware priority，并对 validation / parse-error / timeout 回退信号施加 guardrail，再 materialize 本轮 `mutation.json` 并回写 `attempts / last_selected_round`
- `prepare-round --mutation-key <key>`：显式覆盖自动选择，直接选中指定 entry（仍会校验 entry 可用性）
- `prepare-round --mutation <path>`：兼容旧入口，但会先把手工 spec import/canonicalize 成 registry entry，再 materialize 本轮 `mutation.json`；不再直接把一次性 spec 原样写入 round 目录
- `prepare-round` 会先冻结 round authority（registry entry、materialized mutation、frozen `comparison_baseline`、`recent_feedback_excerpt`），再写出 `worker-contract.json` 并回写 registry bookkeeping；若发现中断残留的 active round，会先按 frozen authority 修复 `mutation.json` / `worker-contract.json` 并对账 registry bookkeeping，再拒绝开启新 round；若 `mutation-registry.json` 已缺失，则会 fail closed 并要求先 `cleanup-round`
- 在没有 active round 时，`prepare-round` 还会先执行最小 stop gate：
  - 连续 `3` 轮已完成 round 都没有产生新的 validation champion，则停止创建新 round
  - 所有 `active` mutation family 都至少尝试过 `1` 次，且当前 run 没有任何最终 `keep`，则停止创建新 round
- 命中 stop gate 或 `max_rounds` 时，`prepare-round` 现在会以正常完成退出并输出 `prepare_round_status: stopped`、`stop_kind`、`stop_reason`；只有真实异常才返回失败
- `run-round`：要求 `agent-report.md` 已写入 round 目录；脚本会重新读取并校验 round 目录里的 `mutation.json`，然后校验 candidate 改动只能触达 `target_paths` 的同级或更窄子路径、且动作类型符合 `allowed_actions`，再提交 candidate 改动、先选择 candidate source suite、再物化到 round-local artifact，随后从 candidate worktree 运行 train / validation suites，并写 round 级 `scoreboard.json`
- `decide-round`：读取“当前比较基线 scoreboard”和本轮 scoreboard，按固定规则先计算 provisional `keep / discard`，必要时在当前 round 下执行 replay；replay 复用与 `run-round` 相同的 suite materialization 语义，再写 `decision.json`，产出 round 级 `feedback-distill.json` 和 run 级 `feedback-ledger.jsonl`，然后调用 promote 或 discard；fixed rule 同时约束 score、parse_error、timeout 与 hard-fail/pass_rate 非回退
- `promote-round`：只允许 fast-forward 语义，把 `champion/<run-id>` 前进到 active candidate commit，然后清理 candidate branch/worktree
- `discard-round`：直接删除 active candidate branch/worktree，不走 `git revert`
- `cleanup-round`：按 `.autoworkflow/autoresearch/<run-id>/runtime.json` 回收中断残留的 active candidate
- `run_autoresearch_loop.py`：自动重复 `prepare-round -> Codex worker -> run-round -> decide-round`；命中 stop 时正常退出 `0`，并输出 `loop_status: stopped`、`stop_kind`、`stop_reason`
- P0.3 仍不实现自动 mutation 搜索、多角色 planner / proposer / critic、或 acceptance 每轮必跑
- candidate 内容改动与 `agent-report.md` 仍由 Codex / subagent 完成；脚本只负责 git 生命周期、评测与 keep / discard

### Autoresearch P0.1 Contract And Data Plane

P0.1 当前代码侧的最小 contract / 数据面行为固定为：

- `autoresearch_contract.py` 会先按 `toolchain/evals/fixtures/schemas/autoresearch-contract.schema.json` 校验 contract JSON
- `load_contract()` 会解析并缓存：
  - `run_id`
  - `train_suites` / `validation_suites` / `acceptance_suites`
  - `mutable_paths` / `frozen_paths`
- suite manifest 的解析顺序是：
  - 先看 contract 文件同目录
  - 再看显式绝对路径
  - 最后回退到 `toolchain/evals/fixtures/suites/`
- `mutable_paths` / `frozen_paths` 会先被归一化为 repo-relative path，再检查是否越过 repo root 或彼此重叠
- `history.tsv` 列顺序当前固定为：
  - `round`
  - `kind`
  - `base_sha`
  - `candidate_sha`
  - `train_score`
  - `validation_score`
  - `train_parse_error_rate`
  - `validation_parse_error_rate`
  - `decision`
  - `notes`
- `autoresearch_scoreboard.py` 当前只聚合 `train` 和 `validation` 两条 lane；lane 指标来自 `run-summary.json` 中 `phase=eval` 的结果
- round 级字段 `rounds_completed` / `best_round` 在 baseline scoreboard 中会初始化为 `0`，后续 round 裁决时更新
- 顶层 `scoreboard.json` 在 round 0 代表 baseline；后续每次 `keep` 后会前移为当前 champion 的比较基线，`discard` 时保持不变

### Autoresearch P0.1 Baseline Flow And Artifacts

P0.1 在共享 CLI 下的实际入口是：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  init \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  baseline \
  --contract /path/to/contract.json
```

当前 `init` / `baseline` 的实际落盘行为是：

- `init`
  - 校验 contract
  - 写 `.autoworkflow/autoresearch/<run-id>/contract.json`
  - 初始化 `history.tsv`
  - 由于共享同一个入口，也会创建 `runtime.json` 作为后续阶段的前向兼容状态文件
- `baseline`
  - 只运行 `train_suites` 和 `validation_suites`
  - 不运行 `acceptance_suites`
  - 会先对原始 contract suite 做 preflight，再把 `train` / `validation` suite 物化到 run-local artifact
  - 会把 `runtime.json.champion_sha` 同步到本次 baseline 的 `baseline_sha`
  - 产物会写到：
    - `.autoworkflow/autoresearch/<run-id>/baseline/materialized-suites/train/`
    - `.autoworkflow/autoresearch/<run-id>/baseline/materialized-suites/validation/`
    - `.autoworkflow/autoresearch/<run-id>/baseline/train/`
    - `.autoworkflow/autoresearch/<run-id>/baseline/validation/`
  - 聚合后写：
    - `.autoworkflow/autoresearch/<run-id>/scoreboard.json`
    - `.autoworkflow/autoresearch/<run-id>/history.tsv`

当前 baseline `scoreboard.json` 的代码行为包括：

- 顶层保留：
  - `run_id`
  - `generated_at`
  - `baseline_sha`
  - `rounds_completed`
  - `best_round`
- lane 级保留：
  - `lane_name`
  - `suite_file`
  - `backend`
  - `judge_backend`
  - `repos_total`
  - `tasks_total`
  - `pass_rate`
  - `timeout_rate`
  - `parse_error_rate`
  - `avg_total_score`
- repo/task 级保留：
  - `repo`
  - `task`
  - `phase`
  - `total_score`
  - `overall`
  - `dimension_feedback`

baseline 写入 `history.tsv` 的约定当前固定为：

- `round = 0`
- `kind = baseline`
- `candidate_sha = -`
- `decision = baseline`

### Autoresearch P0.1 Guardrails

P0.1 当前已固定的校验和边界是：

- contract 必须通过 schema 校验；缺少必填字段会直接失败
- suite manifest 缺失会直接失败
- `mutable_paths` 和 `frozen_paths` 不能重叠
- path 不允许逃出 repo root
- baseline 只消费 `train` / `validation` suites；`acceptance` 当前只作为 contract 引用和后续阶段输入保留
- scoreboard 只基于 `phase=eval` 的结果聚合，不把 skill phase 原始输出直接当分数输入

### Autoresearch P0.1 Verified Scope

当前已验证的范围是：

- contract schema 校验可工作
- 缺字段 contract 会被拒绝
- 缺失 suite manifest 会被拒绝
- `mutable_paths` / `frozen_paths` 重叠会被拒绝
- lane 聚合会正确计算 `pass_rate`、`timeout_rate`、`parse_error_rate`、`avg_total_score`
- repo/task 行会保留 `overall` 与 `dimension_feedback`
- `init` 会写出 `contract.json`、`history.tsv`、`runtime.json`
- `baseline` 会写出 `scoreboard.json`，并追加 baseline 历史行

当前没有承诺或未覆盖的范围是：

- `acceptance_suites` 在 P0.1 baseline 中自动执行
- candidate worktree、round loop、mutation、keep / discard 决策
- qualitative veto 的自动执行逻辑；当前只保留 contract 字段入口

### Autoresearch P2 Batch 1 Single-Prompt Codex Profile

P2 Batch 1 当前不是通用参数搜索系统，只是在现有 `run_autoresearch.py` 上收紧出一个轻量、单 prompt、Codex-only 的 contract profile。

当前代码侧固定了两层映射：

- `target_task -> runner task`
  - `context-routing-skill -> context-routing`
  - `knowledge-base-skill -> knowledge-base`
  - `task-contract-skill -> task-contract`
  - `writeback-cleanup-skill -> writeback-cleanup`
- `target_task -> target_prompt_path`
  - `context-routing-skill -> toolchain/scripts/research/tasks/context-routing-skill-prompt.md`
  - `knowledge-base-skill -> toolchain/scripts/research/tasks/knowledge-base-skill-prompt.md`
  - `task-contract-skill -> toolchain/scripts/research/tasks/task-contract-skill-prompt.md`
  - `writeback-cleanup-skill -> toolchain/scripts/research/tasks/writeback-cleanup-skill-prompt.md`

`autoresearch_contract.py` 当前提供了 P2 的共享边界：

- `AutoresearchContract` 新增可选字段：
  - `target_task`
  - `target_prompt_path`
- 如果 contract 未提供这两个字段，P0/P1 的通用行为保持不变
- 如果提供了其中任一字段，则必须同时提供两者
- `resolve_p2_contract_target()` 会强制校验：
  - `target_task` 必须是上述四个 skill 之一
  - `target_prompt_path` 必须精确匹配固定映射
  - `mutable_paths` 归一化后必须只剩 `[target_prompt_path]`

`run_autoresearch.py` 当前提供了 P2 的 CLI preflight：

- `_validate_p2_preflight()` 会遍历 `train` / `validation` / `acceptance` 三类 suite manifest
- 每个 run 都必须满足：
  - suite 只能覆盖 contract 指定的单个 task
  - `prompt_file` 必须解析到 `contract.target_prompt_path`
  - `backend` 必须是 `codex`
  - `judge_backend` 必须是 `codex`
- `task: all` 在 P2 preflight 下不会被接受为多 prompt 批跑入口
- 允许 suite 不显式写 `prompt_file`，此时会按 task 默认 prompt 路径回填；回填结果仍必须等于 `target_prompt_path`

P2 Batch 1 的命令边界当前固定为：

- 会执行 suite 级 P2 preflight：
  - `init`
  - `baseline`
  - `prepare-round`
  - `run-round`
- 不会做无条件 CLI suite 级 P2 preflight：
  - `decide-round`
- 会执行 suite 级 P2 preflight：
  - `promote-round`
- 不会执行 suite 级 P2 preflight：
  - `discard-round`
  - `cleanup-round`

补充语义：

- `decide-round` 只有在“provisional keep 且 validation 严格高于当前 champion validation”时才会进入 replay
- replay 执行前会复用同一套 P2 preflight，因此 replay-needed 路径不会绕开 `codex -> codex` 与单 prompt 约束
- `promote-round` 当前显式受 P2 preflight 保护
- `discard-round` / `cleanup-round` 仍保留 recovery 语义，不会因为 suite 漂移而 fail-stuck

P2 Batch 1 对 registry / round authority 的额外约束当前也已固定：

- `autoresearch_mutation_registry.py` 会要求 registry entry 的 `target_paths` 必须精确等于 `[contract.target_prompt_path]`
- `autoresearch_round.py` 会要求 materialized round `mutation.json` 的 `target_paths` 也必须精确等于 `[contract.target_prompt_path]`
- 这意味着 Batch 1 当前只允许调一个 prompt 文件，不允许顺手扩大到同 skill 的其他文件或多 prompt 组合

### Autoresearch P2 Batch 1 Verified Scope

当前已验证的范围是：

- contract 可用 `target_task + target_prompt_path` 显式声明“只调一个 prompt”
- 四个 research prompt 的 task/path 固定映射已落地
- `init -> baseline -> prepare-round -> run-round` 会对 P2 单 prompt Codex profile 做 fail-closed preflight
- `prepare-round` 已落地最小 stop gate，不再只依赖 `max_rounds`
- registry entry 与 round mutation 都会被收紧到唯一的 `target_prompt_path`
- `decide-round` 只在 replay-needed 路径复用 P2 preflight，`promote-round` 会显式执行 P2 preflight
- replay 已作为 `decide-round` 的固定脚本子步骤落地，并且 replay 产物会写到 `rounds/round-NNN/replay/`
- replay 通过条件已经收紧为“replay validation 不低于本轮 round validation”，而不是只看 champion baseline
- deterministic P2 smoke 已独立落在 `test_autoresearch_p2_smoke.py`，但当前是 orchestration smoke：覆盖 CLI 主链路与 decision/replay 产物面；lane 执行使用 mock runner（不等价于真实 candidate-side subprocess 跑 `run_skill_suite.py`）
- `test_run_autoresearch.py` 增加了 family-stop guardrail 与 selector 空集区分、replay 前置 P2 preflight 的验收，用于防止 stop rule 被 selector 错误吞掉
- `test_autoresearch_round.py` replay-needed 分支里断言 `provisional_decision` 与 `replay.*` 字段，并保障 replay 再跑产物、scoreboard 与 P2 preflight 一致

当前没有承诺或未覆盖的范围是：

- 同一 run 同时调多个 prompt
- 在 P2 profile 下切换到非 `codex -> codex` backend/judge 组合
- prompt 文本之外的参数搜索
- 更丰富的 persisted family 状态模型

### Autoresearch P0.3 Round Artifacts

单轮 round 目录固定在：

```text
.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/
```

当前脚本会读写或要求存在的最小产物：

- `round.json`：round 编号、`base_sha`、candidate 分支/worktree、当前状态
- `worktree.json`：candidate worktree 路径、分支、`base_sha`、`candidate_sha`、清理时间
- `mutation.json`：本轮 authority mutation spec，包含 `mutation_key`、`attempt`、`fingerprint`、`instruction`、`expected_effect`、`guardrails` 等字段
- `worker-contract.json`：agent-facing 执行信封，压平 candidate worktree、instruction、target_paths、allowed_actions、frozen `comparison_baseline`、`recent_feedback_excerpt`、fingerprints、`materialized_at` 等本轮执行要点
- `agent-report.md`：由 Codex / subagent 写出的本轮内容工作摘要；缺失时 `run-round` 会直接失败
- `train/`：本轮 train suite 的 run artifacts
- `validation/`：本轮 validation suite 的 run artifacts
- `scoreboard.json`：本轮 train / validation 聚合结果
- `decision.json`：固定 keep / discard 规则输出
- `feedback-distill.json`：P1.3 的 round 级 deterministic distilled feedback，记录 delta、signal、flags 与 refs

根目录还会持续维护：

- `contract.json`
- `runtime.json`
- `history.tsv`
- 顶层 `scoreboard.json`：作为“下一轮比较基线”；round 0 时是 baseline，`keep` 后会前移到当前 champion，并在 round 裁决后更新 `rounds_completed` 与 `best_round`
- `feedback-ledger.jsonl`：P1.3 的 run 级 family feedback ledger；同一 `(run_id, round, mutation_id)` 会被 upsert，而不是盲目追加重复行

### Autoresearch P0.3 Guardrails

P0.3 的脚本侧约束当前固定为：

- `prepare-round --mutation-key` 或兼容 `--mutation` 会先 materialize authority `mutation.json`，再冻结 round authority，随后生成 `worker-contract.json`
- materialized `mutation.json` 与 `worker-contract.json` 的 hash 都会写入 `round.json`
- `target_paths` 对 `contract.mutable_paths` 的校验现在是严格子集语义；更宽父路径会被拒绝
- `run-round` 读取 round 目录里的 `mutation.json` 后会重新做同一套 scope 校验，因此不能通过“prepare 后手改 mutation spec”来扩大允许变更范围
- `run-round` 还会校验 `worker-contract.json` 的存在性、hash 和关键 tracing 字段一致性；当前 v2 路径会直接复用 frozen `comparison_baseline` 与 `recent_feedback_excerpt` 重建期望 payload，legacy v1 则仅保留 `transition_compat_weak_checks` 弱校验兼容
- `run-round` 只允许在 round 状态为 `candidate_active` 时执行
- `decide-round` 只允许在 round 状态为 `evaluated` 时执行
- `run-round` 会同时校验两类 candidate 改动：
  - candidate 相对 `base_sha` 的全部已提交差异
  - candidate worktree 当前未提交差异
- 上述两类差异都会统一受 `target_paths`、`allowed_actions`、`frozen_paths` 约束
- 这意味着“先在 candidate worktree 手工提交越界改动，再执行 `run-round`”现在也会被拦截，不再能用 clean worktree 绕过校验

### Autoresearch P0.3 Keep / Discard Rule

`decide-round` 当前是固定脚本规则，不接受模型自由裁决：

- `keep` 同时要求：
  - train `avg_total_score` 严格高于当前比较基线
  - validation `avg_total_score` 不低于当前比较基线
  - train / validation `pass_rate` 不低于当前比较基线
  - train / validation `parse_error_rate` 不高于当前比较基线
  - train / validation `timeout_rate` 不高于当前比较基线
- `discard` 命中任一非回退检查失败即可
- `qualitative_veto_checks` 当前只保留字段入口，不提供奖励权；脚本不会因为定性描述把硬指标无提升的 round 提升为 `keep`

对于 P2 单 Prompt Codex profile，`decide-round` 还带有一个固定 replay 子步骤：

- 只有当本轮 provisional `keep` 且 validation 严格高于当前 champion validation 时，才会触发 replay
- replay 复用当前 round 已固定的 candidate commit 和同一套 train / validation suite materialization 逻辑
- replay 执行前会再次执行 P2 preflight
- replay 目录如果已存在旧产物，会先清空，再重跑 train / validation
- 若 replay validation 低于本轮 round validation，则最终决策会从 provisional `keep` 改写为 `discard`
- replay 结果会写入 `decision.json.replay`，并把 replay scoreboard 写到 `rounds/round-NNN/replay/scoreboard.json`

### Autoresearch P0.3 Verified Scope

当前已验证的范围是：

- `init -> baseline -> prepare-round --mutation-key -> run-round -> decide-round` 主路径可跑通
- `keep` 路径可跑通
- `discard` 路径可跑通
- committed-change bypass 已修复：candidate 先手工提交越界改动时，`run-round` 会失败
- worktree 生命周期仍由脚本控制，不污染当前用户工作树

当前没有承诺或未覆盖的范围是：

- 自动 mutation 搜索
- planner / proposer / critic 等多角色主控
- acceptance suite 每轮必跑
- 对 candidate 分支“每一个中间提交”做逐提交历史审计；当前只校验相对 `base_sha` 的净变更和当前未提交变更

## Backend Adapter Layer

`backends/base.py` 定义最小 backend contract：

- `healthcheck()`：校验可执行文件是否可用
- `build_skill_command()` / `build_eval_command()`：为 skill 与 eval phase 构造命令
- `extract_final_message()`：从 stdout 或 backend 输出文件中提取最终消息

当前 backend 状态：

- `claude`：直接把 prompt 作为命令参数传入；支持 JSON schema judge
- `codex`：通过 stdin 传 prompt，使用 `--output-last-message` 提取最终消息；支持 JSON schema judge
- `opencode`：仅保留 backend slot，healthcheck 会明确返回未实现

## Eval Behavior

eval prompt 由 `common.py` 统一生成：

- 先把 skill 输出注入 task 对应的 eval prompt
- 如果 judge backend 支持 JSON schema，则按 task 动态物化 score-key 与 `dimension_feedback` key 受限的 schema
- schema 在未落盘时写入临时文件；启用 `--save-dir` 时写入 run 目录
- Claude judge 在 schema 模式下会切到 `--output-format json`
- Codex judge 使用 `--output-schema <schema-path>`
- 不支持 schema 的 judge 仍可返回 rubric text，runner 会解析 `scores` 与按维度的 `What Worked / Needs Improvement` 反馈

这里的差异只停留在执行层：task、prompt、summary、artifact 命名都由 unified runner 统一处理。

## Suite Manifest

suite manifest 支持 YAML 或 JSON，当前 fixture 示例见 `toolchain/evals/fixtures/suites/memory-side-skills.v1.yaml`。

最小形态：

```yaml
version: 1
defaults:
  backend: claude
  judge_backend: claude
  with_eval: true
runs:
  - repo: typer
    task: all
```

`--suite` 模式下，`--backend`、`--judge-backend`、`--task`、`--with-eval`、`--prompt-file`、`--eval-prompt-file` 都不再接受命令行覆盖。

当前还提供一组独立 helper，用于把原始 suite 物化成新的 materialized suite：

- `resolve_tmp_exrepos_root(repo_root=...)`：基于显式传入的仓库锚点返回稳定的 `/tmp` exrepo 运行时根目录
- `resolve_materialized_suite_path()`：为物化后的 suite 生成确定性输出路径
- `materialize_suite()`：要求显式传入 `exrepo_root` 或 `repo_root`；把 suite 中的 bare repo name 重写为 TMP exrepo 绝对路径，并把 `prompt_file` / `eval_prompt_file` 改写为基于源 suite 目录解析后的绝对路径
- helper 不会原地修改源 suite，也不会把 `/tmp` 路径写进 authority 状态
- `run_autoresearch.py baseline` 与 `autoresearch_round.py` 的 `run-round / replay` 已复用这组 helper；materialized suite 会落到 run-local artifact，而不是 authority 状态
- `run_skill_suite.py` 的 direct `--repo` / `--suite` 模式本身没有被改成自动 materialize；如果绕过 autoresearch 主链，仍需保证输入 suite 在 runner 侧可解析
- deterministic 覆盖当前已固定到四个断言面：
  - `test_exrepo_runtime.py`：helper 级 YAML / JSON 路径重写与源 manifest 不变性
  - `test_run_skill_suite.py`：runner 对 materialized suite 的绝对路径消费
  - `test_run_autoresearch.py`：baseline lane 对 materialized suite 的消费
  - `test_autoresearch_round.py`：round / replay lane 物化与 replay 执行失败后的 discard 语义

## Examples

单 repo，运行单个 task：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend claude \
  --task context-routing
```

单 repo，Codex 执行 skill，Claude 执行 eval，并保存结果：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend codex \
  --task all \
  --with-eval \
  --judge-backend claude \
  --save-dir /tmp/skill-evals
```

live smoke 若要贴近日常使用，建议保留默认 `--timeout 300`，或按需要显式放宽：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend codex \
  --task context-routing \
  --with-eval \
  --save-dir /tmp/skill-evals \
  --timeout 300
```

单 repo，全量 task 并发跑四个 skills：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --repo typer \
  --backend codex \
  --task all \
  --with-eval \
  --jobs 4 \
  --save-dir /tmp/skill-evals
```

按 suite 执行：

```bash
python3 toolchain/scripts/research/run_skill_suite.py \
  --suite memory-side-skills.v1.yaml \
  --save-dir /tmp/skill-evals
```

backend acceptance matrix：

```bash
python3 toolchain/scripts/research/run_backend_acceptance_matrix.py \
  --repo typer \
  --save-dir /tmp/backend-acceptance
```

autoresearch P0.1 初始化：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  init \
  --contract /path/to/contract.json
```

autoresearch P0.1 baseline：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  baseline \
  --contract /path/to/contract.json
```

autoresearch P0.3 准备一轮 candidate：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  prepare-round \
  --contract /path/to/contract.json
```

如需显式覆盖自动选择：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  prepare-round \
  --contract /path/to/contract.json \
  --mutation-key text_rephrase:demo:intro-tighten-v1
```

先读取 round 目录里的 `worker-contract.json`，再在 candidate worktree 内完成允许的改动，并把 `agent-report.md` 写到：

```text
.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/worker-contract.json
.autoworkflow/autoresearch/<run-id>/rounds/round-NNN/agent-report.md
```

随后运行 round 评测与裁决：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  run-round \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  decide-round \
  --contract /path/to/contract.json
```

autoresearch P0.2 promote / discard / cleanup：

```bash
python3 toolchain/scripts/research/run_autoresearch.py \
  promote-round \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  discard-round \
  --contract /path/to/contract.json

python3 toolchain/scripts/research/run_autoresearch.py \
  cleanup-round \
  --contract /path/to/contract.json
```

Claude 兼容壳：

```bash
python3 toolchain/scripts/research/run_claude_skill_eval.py \
  --repo typer \
  --task context-routing \
  --with-eval
```

## P1.3 Regression Checklist

P1.3 回归建议固定分三层执行：

- 静态检查：

```bash
python3 -m py_compile \
  toolchain/scripts/research/run_autoresearch.py \
  toolchain/scripts/research/autoresearch_feedback_distill.py \
  toolchain/scripts/research/autoresearch_mutation_registry.py \
  toolchain/scripts/research/autoresearch_worker_contract.py \
  toolchain/scripts/research/autoresearch_selector.py \
  toolchain/scripts/research/test_autoresearch_feedback_distill.py \
  toolchain/scripts/research/test_autoresearch_mutation_registry.py \
  toolchain/scripts/research/test_autoresearch_worker_contract.py \
  toolchain/scripts/research/test_autoresearch_selector.py \
  toolchain/scripts/research/test_exrepo_runtime.py \
  toolchain/scripts/research/test_run_skill_suite.py \
  toolchain/scripts/research/test_autoresearch_round.py \
  toolchain/scripts/research/test_run_autoresearch.py \
  toolchain/scripts/research/test_autoresearch_p1_1_smoke.py \
  toolchain/scripts/research/test_autoresearch_p1_3_smoke.py \
  toolchain/scripts/research/test_autoresearch_p2_smoke.py
```

- 白盒测试：

```bash
python3 -m unittest \
  toolchain/scripts/research/test_autoresearch_feedback_distill.py \
  toolchain/scripts/research/test_autoresearch_mutation_registry.py \
  toolchain/scripts/research/test_autoresearch_worker_contract.py \
  toolchain/scripts/research/test_autoresearch_selector.py \
  toolchain/scripts/research/test_exrepo_runtime.py \
  toolchain/scripts/research/test_run_skill_suite.py \
  toolchain/scripts/research/test_autoresearch_round.py \
  toolchain/scripts/research/test_run_autoresearch.py \
  toolchain/scripts/research/test_autoresearch_p1_1_smoke.py \
  toolchain/scripts/research/test_autoresearch_p1_3_smoke.py \
  toolchain/scripts/research/test_autoresearch_p2_smoke.py
```

- smoke 测试覆盖：
  - legacy P1 路径由 `test_autoresearch_p1_1_smoke.py` 与 `test_autoresearch_p1_3_smoke.py` 固定
  - `init -> baseline -> prepare-round(auto select) -> run-round -> decide-round`
  - `prepare-round --mutation-key` 显式覆盖自动选择
  - stop gate / `max_rounds` 命中时 `prepare-round` 正常停止，不再伪装成失败
  - all-unselectable 时 `prepare-round` 仍然失败
  - tamper `worker-contract.json` 时 `run-round` 失败
  - pending duplicate fingerprint 会在 auto select 时被跳过
  - `decide-round` 会写出 `feedback-distill.json` 和 `feedback-ledger.jsonl`
  - round 2 auto select 会优先复用近期 positive signal family，而不是盲目回到最低 attempts 规则
  - P2 orchestration smoke 由 `test_autoresearch_p2_smoke.py` 固定（mock lane 执行，只覆盖 CLI 编排与 decision/replay 产物面）
  - family-stop 命中时会先于 `No selectable mutation entries` 触发，避免把 stop gate 误判成 selector 空集

P1.3 selector 规则（feedback-aware，但仍保持脚本主控）固定为：

- 只考虑 `status == active` 的 entry
- 跳过 `attempts >= max_candidate_attempts_per_round` 的 entry
- 跳过 fingerprint 与当前 pending round 冲突的 entry
- 无 ledger 时，按 `attempts -> registry 原始顺序 -> mutation_key` 选最小项
- 有 ledger 时，先按 `signal band -> attempts -> registry 原始顺序 -> mutation_key` 排序
- `signal band` 固定为：
  - `recent_positive_signal`
  - `no_feedback_history`
  - `guided_mixed_retry`
  - `mixed_signal_retry`
  - `guardrail_capped_mixed_retry`
  - `latest_negative_signal`
  - `guardrail_blocked_retry`
  - `sustained_regression_deprioritized`
- selector 返回 `mutation_key / attempt / selection_reason / scheduler_reason / selection_index`

P1.2 worker-contract 形状当前固定为：

- 身份：`run_id / round / mutation_id / mutation_key / attempt`
- 执行面：`base_sha / candidate_branch / candidate_worktree / agent_report_path`
- 变更边界：`target_paths / allowed_actions / guardrails / instruction / expected_effect`
- 只读上下文：`objective / target_surface / comparison_baseline / recent_feedback_excerpt`
- 校验锚点：`contract_fingerprint / mutation_fingerprint / materialized_at`

P1.2 常见失败语义：

- `Missing mutation registry ...`：未提供 `--mutation` 且 run-local registry 缺失
- `No selectable mutation entries ...`：entry 全部 disabled/exhausted
- `mutation.json does not match frozen round authority snapshot ...`：round mutation 与 frozen authority 不一致
- `mutation.json does not match hash ...`：round mutation 被篡改
- `worker-contract.json does not match hash ...`：worker contract 被篡改
- `worker-contract.json does not match authoritative round/mutation/worktree state ...`：hash 通过但关键 tracing 字段与 authority 状态不一致
- `Missing worker contract ...`：prepare 后缺少 worker-contract 产物
- `Missing agent report ...`：run-round 前未写入 `agent-report.md`

## Saved Artifacts

默认不落盘。传 `--save-dir` 后，每轮 run 会生成一个独立子目录，并写入：

- `*.prompt.txt`：实际发送给 backend 的 prompt 文本
- `*.response.md`：展示口径的响应副本，内容等于 `final_message`，若没有则回退为 `raw_stdout`
- `*.final.txt`：backend 提取出的最终消息；若 backend 没有单独 final message，可为空文件
- `*.raw.stdout.txt`：进程原始 stdout
- `*.raw.stderr.txt`：进程原始 stderr，仅在 stderr 非空时写入
- `*.stderr.txt`：兼容保留的 stderr 副本，仅在 stderr 非空时写入
- `*.eval-schema.<judge>.json`：本次 eval 实际使用的 task-scoped schema，仅 schema judge 写入
- `*.structured.json`：规范化后的 eval 结构化结果；其中除了分数，还会保留每个维度的 `dimension_feedback`
- `*.meta.json`：单条结果元数据，含 command、returncode、timing、schema_file、parse_error、artifacts
- `run-summary.json`：整轮汇总，含 `summary_schema` 路径、suite 来源和所有 result 记录

artifact 文件名按序号、repo、task、phase、backend 组合生成，例如：

- `01.typer.context-routing.skill.claude.*`
- `02.typer.context-routing.eval.codex-judge-claude.*`

## Minimal Constraints

- 脚本目录只放 runner 与 prompt，不把研究输出直接写回这里
- 需要产物时显式传 `--save-dir`
- 研究输出目录应放在脚本目录之外
- 旧的 Claude-only 调用可以继续走兼容壳，但新的行为应以 `run_skill_suite.py` 为准
- live acceptance matrix 依赖真实 backend，可有成本与波动，不应当作快速 CI 或 cheap regression
- 开启并发时，runner 会保持结果打印顺序、artifact 编号和 `run-summary.json` 顺序稳定；如果需要最保守的 backend 行为，可退回 `--jobs 1`
