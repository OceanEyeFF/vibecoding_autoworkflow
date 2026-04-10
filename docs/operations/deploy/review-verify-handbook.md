---
title: "Review / Verify 承接位"
status: active
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---
# Review / Verify 承接位

> 目的：把 `plan -> implement -> verify -> review -> writeback` 收成一个 repo-local、可复用、可引用的复核入口。本文只承接执行阶段的最小复核动作，不承接长期真相本体。

本页属于 [Deploy / Verify / Maintenance](./README.md) 路径簇。

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

### 1. 变更范围

- diff 是否只覆盖当前任务
- 是否触碰了不在 scope 内的文件层
- 是否存在未声明的新目录、新入口或新规则

### 2. 规则同步

- 如果改了 root / partition / path 规则，是否同步 foundations 和治理检查
- 如果改了 `AGENTS.md` 或执行流程，是否同步本文
- 如果改了 deploy / adapter 行为，是否同步对应 operations runbook
- 如果改了 `docs/knowledge/*/skills/`、`product/*/skills/*/`、`product/*/adapters/*/skills/*/` 或 `docs/operations/prompt-templates/`，是否仍保持四段式分工：合同层、canonical executable layer、backend adapter layer、compatibility shim / usage bridge layer
- 如果改了 `product/*/adapters/*/skills/*/SKILL.md`，是否仍保持 thin wrapper（`Canonical Source / Backend Notes / Deploy Target`）而没有重新复制 canonical 语义正文
- 如果改了 `product/*/skills/*/SKILL.md`，是否保持最小 executable body + `references/entrypoints.md`，而没有吸收 repo-local execution template 内容
- 如果改了 `docs/operations/prompt-templates/`，是否仍只承接 compatibility shim，并回链对应 `product/harness-operations/` canonical source 与 `docs/knowledge/` 主线入口

### 3. 验证结果

按改动面选择最小验证集：

- 根目录、路径、分层、hidden/state 规则变更
  - `python3 toolchain/scripts/test/folder_logic_check.py`
  - `python3 toolchain/scripts/test/path_governance_check.py`
  - `python3 toolchain/scripts/test/governance_semantic_check.py`
- skills / templates 分层规则变更
  - `python3 toolchain/scripts/test/path_governance_check.py`
  - `python3 toolchain/scripts/test/governance_semantic_check.py`
- closeout / gate / backfill 变更
  - `python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`
  - 对应的最小 pytest
- adapter / deploy 变更
  - `python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend <backend>`

### 3.1 修复完整性

如果本轮是 bugfix、review comment 响应或回归修复，额外确认：

- 修复是否覆盖根因或至少覆盖同一条执行链上的相邻状态，而不只是让当前断言通过
- 是否检查了相邻 phase / state / recovery path，不把错误转移到下一步或旁路入口
- 是否检查了 operator-facing 视图、状态聚合、CLI 返回码和文档承诺之间仍然一致
- 是否补了能锁住该问题及其直接相邻变体的回归测试
- 是否确认修复后不会把已有 healthy path、dirty state path 或 malformed artifact path 重新打坏

### 4. 回写要求

- 已验证结果写进 `docs/knowledge/`
- repo-local 维护动作写进 `docs/operations/`
- 不把临时推理、未验证猜测或执行噪音写成长期真相
- 如果需要固定输出结构，优先复用现有模板而不是新发明格式

## 四、完成标准

当下面几项都满足时，可以认为 review/verify 收口完成：

- 变更范围清楚
- 必要验证已跑
- review 没有发现未处理风险
- 同步文档已经更新
- writeback 已完成
- 如果是修复类任务，相关相邻状态和回归路径也已验证，没有留下新的已知问题源

## 五、相关文档

- [AGENTS.md](../../../AGENTS.md)
- [路径与文档治理检查运行说明](./path-governance-checks.md)
- [Autoresearch closeout acceptance gate](../autoresearch/closeout/acceptance-gate.md)
- [Deploy Runbook](./deploy-runbook.md)
- [Skill Deployment 维护流](./skill-deployment-maintenance.md)
- [Branch / PR 治理规则](./branch-pr-governance.md)
