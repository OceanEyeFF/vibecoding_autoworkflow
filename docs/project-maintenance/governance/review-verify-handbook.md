---
title: "Review / Verify 治理入口"
status: active
updated: 2026-05-08
owner: aw-kernel
last_verified: 2026-05-08
---
# Review / Verify 治理入口

> 目的：把 `plan -> implement -> verify -> review -> writeback` 收成一个 repo-local、可复用、可引用的复核入口。本文只说明执行阶段的最小复核动作，不作为长期真相本体。

## 一、适用范围

在任务收口前、改完代码后、或需要固定 review checklist 时先读本文；不适用作 canonical truth、长期架构设计或开发计划。

## 二、默认流程

`plan -> implement -> verify -> review -> writeback`；先确认目标与范围，只改当前任务不扩边界，`verify` 先于 `review`，`writeback` 只录已验证事实。修复类任务必须检查相邻状态、恢复路径、operator-facing 语义和脏数据场景。

## 三、推荐复核清单

默认覆盖性能、架构、安全、质量、测试五个独立面；docs-only 或 governance-only 变更需显式标出不适用面及理由。

### 1. 变更范围

- diff 是否只覆盖当前任务，是否触碰不在 scope 内的文件层，是否存在未声明的新目录/入口/规则

### 2. 规则同步

- root/partition/path/hidden-layer 变更需同步 foundations、关键入口页和治理检查
- AGENTS.md 或执行流程变更需同步本文
- runbook/usage-help/testing/Harness 长文变更需说明当前页类型（入口/runbook/合同/指导）并清理重复正文
- deploy/adapter 变更需同步对应 runbook、maintenance 与 usage-help，口径保持 destructive reinstall model
- package/release/version/VCS baseline 事实变更需调用 `doc-catch-up-worker-skill` 做 version fact sync；pre-publish 只同步 source version facts 与 VCS tracking facts，post-publish registry verification 后才能同步 published version facts
- docs/harness/、product/harness/skills/ 或 adapters 变更需保持合同层与 executable layer 分工
- branch/PR/baseline 规则变更需从 `origin/HEAD` 或 Worktrack Contract 的 `baseline_branch` 取值，不写死默认分支名
- 退役/删除文档域需同步入口页、旧路径引用和治理检查
- SKILL.md 变更需保持最小 executable body；已退役 references 需同步清理
- product/.aw_template/ 变更只承接 scaffold 模板，不生长 canonical truth 或运行状态
- docs/harness/workflow-families/ 变更需明确文档真相层定位，对 product/harness/ 只能当下游 executable root

### 3. 验证结果

按改动面选择最小验证集；所有 Python 命令默认使用 `PYTHONDONTWRITEBYTECODE=1 python3 ...`。

- 根目录/路径/分层/hidden/state 规则变更：`folder_logic_check.py` + `path_governance_check.py` + `governance_semantic_check.py`
- skills/templates 分层规则变更：`path_governance_check.py` + `governance_semantic_check.py`
- branch/PR/baseline 或 hook 变更：`git symbolic-ref` + `bash -n pre-push` + dry-run
- `.aw_template`/`.aw/` scaffold 变更：`path_governance_check.py` + `governance_semantic_check.py`
- closeout/gate/backfill 变更：`closeout_acceptance_gate.py --json` + 对应最小 pytest；closeout 按 `scope_gate -> spec_gate -> static_gate -> cache_gate -> test_gate -> smoke_gate` 收口；`cache_gate` 扫描 `docs/`、`product/`、`toolchain/` 和 `tools/` 下的 Python / pytest 运行缓存；`scope_gate` 允许 root `README.md` 与 `product/.aw_template/`；`test_gate` 运行 closeout/folder/path/semantic/adapter 回归 + deploy package Node unit tests + npm packlist + publish dry-run + tarball smoke
- deploy mapping/payload contract 变更：`test_agents_adapter_contract.py`；改 gate 链路再补 `closeout_acceptance_gate.py --json`
- adapter/deploy 变更：`test_agents_adapter_contract.py` + npm test + smoke + 双端 `npm pack --dry-run --json` + publish dry-run + tarball 全命令 smoke（diagnose/update/install/verify）+ 隔离 target repo full smoke
- Harness runtime 观察或 operator-facing runbook 变更：先跑对应 deploy/adapter 最小验证，再按 [Codex Post-Deploy Behavior Tests](../testing/codex-post-deploy-behavior-tests.md) 做真实观察（不用 mock smoke 替代）

### 3.1 修复完整性

bugfix/review 响应/回归修复需覆盖根因或相邻执行链状态，检查相邻 phase/state/recovery path、operator-facing 视图与 CLI 返回码一致性；补回归测试，不破坏已有 healthy/dirty/malformed path；未声明支持的 nested target layout 标成 contract expansion topic 而非 patch bug。

### 4. 回写要求

已验证结果写进 `docs/harness/` 或 `docs/project-maintenance/`；不把临时推理写成长期真相；优先复用现有模板；文档精简时需说明保留内容、删除内容、以及入口与合同是否清晰。

## 四、完成标准

变更范围清楚、必要验证已跑、review 无未处理风险、同步文档已更新、writeback 已完成；修复类任务还需验证相邻状态与回归路径。收口说明遵循[全局语言风格](./global-language-style.md)。

## 五、相关文档

- [AGENTS.md](../../../AGENTS.md)
- [路径与文档治理检查运行说明](./path-governance-checks.md)
- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Branch / PR 治理规则](./branch-pr-governance.md)
