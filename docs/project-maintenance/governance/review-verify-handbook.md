---
title: "Review / Verify 治理入口"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Review / Verify 治理入口

> 目的：把 `plan -> implement -> verify -> review -> writeback` 收成一个 repo-local、可复用、可引用的复核入口。本文只承接执行阶段的最小复核动作，不承接长期真相本体。

本页属于 [Governance](./README.md) 路径簇。

## 一、适用范围

本文适合在这些场景先读：

- 任务即将收口，需要确认有没有漏同步
- 你已经改完代码或文档，准备做最后检查
- 你需要一个固定的 review checklist，而不是临时口头约定

本文不适合拿来当：

- canonical truth 文档
- 长期架构设计文档
- 开发计划本身

## 二、默认流程

1. `plan`
2. `implement`
3. `verify`
4. `review`
5. `writeback`

执行原则：

- 先确认目标、范围、非目标、验收和风险
- 只改当前任务，不顺手扩边界
- `verify` 先于 `review`
- `review` 只审已经验证过的改动
- `writeback` 只记录已验证事实
- 修复类任务不能只压住当前症状；必须检查相邻状态、恢复路径、operator-facing 语义和已知脏数据场景，避免引入新的问题源，并尽量把修复做完整

## 三、推荐复核清单

默认 review 至少覆盖五个互相独立的面：

- 代码性能 review：复杂度、重复工作、I/O、资源使用、可扩展性风险
- Repo 架构 review：目录层级、模块归属、依赖方向、truth/source/deploy target 边界
- 代码安全 review：权限边界、外部输入、敏感数据、注入面、破坏性动作保护
- 代码质量 review：可维护性、可读性、错误处理、恢复路径、operator-facing 语义
- 测试 review：验收覆盖、回归覆盖、验证可信度、缺失测试或过期证据风险

docs-only 或 governance-only 变更也要显式标出不适用的 review 面及理由，不能把未覆盖维度默认为通过。

### 1. 变更范围

- diff 是否只覆盖当前任务
- 是否触碰了不在 scope 内的文件层
- 是否存在未声明的新目录、新入口或新规则

### 2. 规则同步

- 如果改了 root / partition / path / hidden-layer 规则，是否同步 foundations、关键入口页和治理检查
- 如果改了 `AGENTS.md` 或执行流程，是否同步本文
- 如果改了 runbook、usage-help、testing guide 或 Harness 长文的承载边界，是否说明当前页属于入口页、runbook、合同页还是指导文档，并清理重复正文、旧入口和双份主线
- 如果改了 deploy / adapter 行为，是否同步对应 `docs/project-maintenance/deploy/` runbook、maintenance 与 usage-help，并确保文档口径仍是 destructive reinstall model
- 如果改了 `docs/harness/`、`product/harness/skills/*/` 或 `product/harness/adapters/*/skills/*/`，是否仍保持合同层与 executable layer 分工
- 如果改了 branch / PR / baseline 规则，是否仍从 `origin/HEAD` 或 Worktrack Contract 的 `baseline_branch` 取值，而不是在技能、hook 或 runbook 中写死默认分支名；当前仓库已验证 baseline 为 `origin/HEAD -> master`
- 如果退役或删除文档域，是否同步最近入口页、旧路径引用和治理检查，避免留下双主线或 required entrypoint 影子
- 如果改了 `product/*/skills/*/SKILL.md`，是否仍保持最小 executable body；若出现对已退役 `references/entrypoints.md` 的引用或文件回流，是否同步清理并更新对应治理检查与引用口径
- 如果改了 `product/.aw_template/`，是否仍只承接 `.aw/` scaffold 模板或受控待迁移模板，而没有长出 canonical truth、backend wrapper 或运行状态
- 如果改了 `docs/harness/workflow-families/`，是否仍明确它承接的是文档真相层；若链接 `product/harness/`，也只能把它当作下游 executable root，而不是 ontology 上游

### 3. 验证结果

按改动面选择最小验证集：

运行本仓库内的 Python 验证、部署或辅助命令时，默认使用 `PYTHONDONTWRITEBYTECODE=1 python3 ...`。这样可以避免验证过程在 `product/`、`docs/`、`toolchain/` 或 `tools/` 下生成 `.pytest_cache`、`__pycache__`、`.pyc` 或 `.pyo` 运行缓存；如果必须用其他 Python launcher，也应保留等价的 `PYTHONDONTWRITEBYTECODE=1` 环境变量。

- 根目录、路径、分层、hidden/state 规则变更
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py`
- skills / templates 分层规则变更
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py`
- branch / PR / baseline 规则或 hook 变更
  - `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`
  - `bash -n toolchain/scripts/git-hooks/pre-push`
  - 用 `refs/heads/<baseline_branch>` 输入 dry-run 覆盖 hook 阻断路径
- `.aw_template` 初始化工具或 `.aw/` legacy scaffold profile 生成逻辑变更
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/aw_scaffold.py validate --profile first-wave-minimal`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_aw_scaffold.py'`
- closeout / gate / backfill 变更
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`
  - 对应的最小 pytest
  - closeout acceptance gate 当前按 `scope_gate -> spec_gate -> static_gate -> cache_gate -> test_gate -> smoke_gate` 顺序收口；其中 `cache_gate` 会扫描 `docs/`、`product/`、`toolchain/` 和 `tools/` 下的 `.pytest_cache`、`__pycache__`、`.pyc` 与 `.pyo` 运行缓存。
  - closeout `scope_gate` 允许 root `README.md`，因为它是根 `aw-installer` package envelope 的 npm README surface；也允许 `product/.aw_template/`，因为它是 `.aw/` scaffold 模板源码层。
  - closeout `test_gate` 会运行 closeout gate、folder logic、path governance、semantic governance、agents adapter contract 回归测试、deploy regression unittest suite、deploy package Node unit tests、Repo Analysis contract check、本地 npm deploy package 与根 `aw-installer` package envelope 的 `npm pack --dry-run --json` packlist 检查、根 package publish dry-run及其 `prepublishOnly` guard、临时 `.tgz` help/version/TUI non-interactive guard/diagnose/update dry-run/install/verify/update apply tarball smoke，以及 repo-local Python reference `adapter_deploy.py` / `harness_deploy.py` 的 `agents` deploy verify。
- deploy mapping / payload contract 变更
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_agents_adapter_contract.py`
  - 如同时改了 gate 链路，再补 `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`
- adapter / deploy 变更
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_agents_adapter_contract.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'`
  - `npm --prefix toolchain/scripts/deploy test --silent`
  - `npm --prefix toolchain/scripts/deploy run smoke --silent`
  - 在 `toolchain/scripts/deploy/` 内运行 `npm pack --dry-run --json`
  - 在仓库根目录运行 `npm pack --dry-run --json`
  - 在仓库根目录运行 `npm run publish:dry-run --silent`
  - 从临时 `npm pack --pack-destination` 产物运行 `npm exec --package <tgz> -- aw-installer --help`
  - 设置 `AW_HARNESS_REPO_ROOT=<repo-root>` 后，从同一个临时 `.tgz` 运行 `aw-installer diagnose --backend agents --json`
  - 设置 `AW_HARNESS_REPO_ROOT=<repo-root>` 后，从同一个临时 `.tgz` 运行 `aw-installer update --backend agents --json`
  - 从根 package 临时 `.tgz` 在隔离 target repo 中运行无 `AW_HARNESS_REPO_ROOT` 的 `aw-installer diagnose --backend agents --json`、`aw-installer update --backend agents --json`、`aw-installer install --backend agents`、`aw-installer verify --backend agents` 和 `aw-installer update --backend agents --yes`；该 smoke 的验收口径是 source payload 来自 package 内，target repo root 来自当前工作目录，`AW_HARNESS_TARGET_REPO_ROOT` 与 `--agents-root` 只作为显式 target override
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_governance_semantic_check.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents`
  - `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py verify --backend agents`
- Harness runtime 观察或 operator-facing runbook 变更
  - 先跑对应 deploy / adapter 最小验证
  - 再按 [Codex Post-Deploy Behavior Tests](../testing/codex-post-deploy-behavior-tests.md) 做真实手动观察；该路径不是 cheap deterministic gate，不用 mock smoke 替代

### 3.1 修复完整性

如果本轮是 bugfix、review comment 响应或回归修复，额外确认：

- 修复是否覆盖根因或至少覆盖同一条执行链上的相邻状态，而不只是让当前断言通过
- 是否检查了相邻 phase / state / recovery path，不把错误转移到下一步或旁路入口
- 是否检查了 operator-facing 视图、状态聚合、CLI 返回码和文档承诺之间仍然一致
- 是否补了能锁住该问题及其直接相邻变体的回归测试
- 是否确认修复后不会把已有 healthy path、dirty state path 或 malformed artifact path 重新打坏
- 如果本轮 review 的问题建立在某种路径形态或输入形态上，是否先确认该形态已经被当前 contract 和文档声明支持；对 deploy / adapter 任务，未声明支持的 nested target layout 应标成 contract expansion topic，而不是直接当作当前 patch bug

### 4. 回写要求

- 已验证结果优先写进 `docs/harness/` 或 `docs/project-maintenance/`
- repo-local 维护动作写进 `docs/project-maintenance/`
- 不把临时推理、未验证猜测或执行噪音写成长期真相
- 如果需要固定输出结构，优先复用现有模板而不是新发明格式
- 如果本轮是文档精简，收口时至少说明：
  - 当前页保留的高价值内容是什么
  - 删除或下沉了哪些重复内容
  - 唯一入口和唯一合同是否仍然清晰

## 四、完成标准

当下面几项都满足时，可以认为 review/verify 收口完成：

- 变更范围清楚
- 必要验证已跑
- review 没有发现未处理风险
- 同步文档已经更新
- writeback 已完成
- 如果是修复类任务，相关相邻状态和回归路径也已验证，没有留下新的已知问题源

补充要求：

- 面向 operator 或协作者的人读收口说明，默认遵循 [全局语言风格](./global-language-style.md)，先交付结论与可执行性，再补充解释

## 五、相关文档

- [AGENTS.md](../../../AGENTS.md)
- [路径与文档治理检查运行说明](./path-governance-checks.md)
- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Branch / PR 治理规则](./branch-pr-governance.md)
