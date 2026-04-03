---
title: "Review / Verify 承接位"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Review / Verify 承接位

> 目的：把 `plan -> implement -> verify -> review -> writeback` 收成一个 repo-local、可复用、可引用的复核入口。本文只承接执行阶段的最小复核动作，不承接长期真相本体。

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

## 三、推荐复核清单

### 1. 变更范围

- diff 是否只覆盖当前任务
- 是否触碰了不在 scope 内的文件层
- 是否存在未声明的新目录、新入口或新规则

### 2. 规则同步

- 如果改了 root / partition / path 规则，是否同步 foundations 和治理检查
- 如果改了 `AGENTS.md` 或执行流程，是否同步本文
- 如果改了 deploy / adapter 行为，是否同步对应 operations runbook

### 3. 验证结果

按改动面选择最小验证集：

- 根目录、路径、分层、hidden/state 规则变更
  - `python3 toolchain/scripts/test/folder_logic_check.py`
  - `python3 toolchain/scripts/test/path_governance_check.py`
  - `python3 toolchain/scripts/test/governance_semantic_check.py`
- closeout / gate / backfill 变更
  - `python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`
  - 对应的最小 pytest
- adapter / deploy 变更
  - `python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend <backend>`

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

## 五、相关文档

- [AGENTS.md](../../AGENTS.md)
- [路径与文档治理检查运行说明](./path-governance-checks.md)
- [Autoresearch closeout acceptance gate](./autoresearch-closeout-acceptance-gate.md)
- [Deploy Runbook](./deploy-runbook.md)
- [Skill Deployment 维护流](./skill-deployment-maintenance.md)
- [Branch / PR 治理规则](./branch-pr-governance.md)
