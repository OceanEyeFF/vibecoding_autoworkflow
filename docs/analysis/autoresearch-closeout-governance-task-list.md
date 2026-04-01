---
title: "Autoresearch：收口治理任务清单"
status: active
updated: 2026-04-02
owner: aw-kernel
last_verified: 2026-04-02
---
# Autoresearch：收口治理任务清单

> 说明：本文是当前 `autoresearch` 收口治理期的执行任务清单，用来指导这轮治理工程期间的实际行动、依赖顺序和完成标准。它只覆盖收口治理，不覆盖下一阶段 implementation。

## 一、执行顺序

当前建议按下面顺序推进：

1. `收口边界与 authority`
2. `运行产物保留与归档规则`
3. `文档入口与生命周期清理`
4. `证据编目与命名纪律`
5. `收口检查与验收门`

说明：

- `文档入口与生命周期清理` 可以和 retention 初稿并行启动
- `证据编目与命名纪律` 必须建立在 retention 规则基本稳定之后
- `收口检查与验收门` 只能最后收尾

## 二、任务清单

### A. 收口边界与 authority

#### G-001：冻结收口期变更边界

- 要做什么：写一页 `allowed / forbidden changes` 和 `closeout scope freeze`
- 依赖：无
- 完成标准：不会再有人追问“这件事现在到底算不算 closeout scope”

#### G-002：明确治理 authority

- 要做什么：列清楚谁能拍板 `superseded / archive / delete / retain / waiver`
- 依赖：`G-001`
- 完成标准：每类治理动作都有明确 authority，而不是谁都能改或谁都不敢改

#### G-003：建立 waiver 规则

- 要做什么：定义少量例外项如何申请、谁批准、如何记录
- 依赖：`G-002`
- 完成标准：例外项有正式口径，不再靠默认放行

### B. 运行产物保留与归档规则

#### G-101：建立 retention baseline

- 要做什么：定义 `.autoworkflow` artifact 的 `必留 / 可归档 / 可删除` 三层规则
- 依赖：`G-001`、`G-002`
- 完成标准：每类 artifact 都能回答“留 / 归档 / 删，谁决定，为什么”

#### G-102：细化关键目录规则

- 要做什么：单独写清 `autoresearch-archive`、`manual-runs`、`acceptance-worktrees` 的保留条件
- 依赖：`G-101`
- 完成标准：关键目录不再共享一套过粗的保留规则

#### G-103：建立 cleanup log 规则

- 要做什么：规定所有清理动作至少记录“删了什么、为什么删、是否可恢复”
- 依赖：`G-101`
- 完成标准：清理动作不再是无痕操作

#### G-104：建立容量预算与超限提醒

- 要做什么：给 `.autoworkflow` 设一个简单容量预算和超限提醒口径
- 依赖：`G-101`
- 完成标准：artifact 膨胀有可见信号，而不是等目录失控才发现

#### G-105：执行一次真清理演练

- 要做什么：按 retention baseline 跑一轮真实清理，再修正规则和 runbook
- 依赖：`G-102`、`G-103`
- 完成标准：规则已经执行过一次，不再只是纸面约定

#### G-106：落盘 artifact hygiene runbook

- 要做什么：把 retention、cleanup、容量预算和日志规则写进 repo-local runbook
- 依赖：`G-105`
- 完成标准：后续同类动作不再依赖口头记忆

### C. 文档入口与生命周期清理

#### G-201：校准 analysis 当前入口

- 要做什么：更新 `docs/analysis/README.md` 当前入口、bucket 和状态清单
- 依赖：`G-001`
- 完成标准：当前 active 入口和历史 lineage 入口不再混在一起

#### G-202：退役旧 planning 并补前跳说明

- 要做什么：给已替代文档补 `superseded`、`superseded_by / successor / lineage` 说明
- 依赖：`G-201`
- 完成标准：旧 planning 不再只是“退役”，而是能明确告诉读者现在该看哪里

#### G-203：补非默认入口警示

- 要做什么：给保留但非默认入口的文档补“不是当前执行入口”提示
- 依赖：`G-201`
- 完成标准：可读文档不会再被误当当前主入口

#### G-204：固化阶段复盘与运行观察

- 要做什么：补一页简短复盘或在现有文档中固化截至收口日的运行观察
- 依赖：`G-201`
- 完成标准：本阶段已经验证过的事实有稳定落点

#### G-205：建立唯一 closeout 主文档

- 要做什么：建立唯一 closeout 主文档或 summary entry，串起主入口、runbook、deferred 项和 gate
- 依赖：`G-201`
- 完成标准：新进入者只看一页就能知道收口期现在的主入口

#### G-206：补承接回链并审视最短路径

- 要做什么：给 analysis 文档补承接层回链，并检查仓库入口最短路径是否仍然清楚
- 依赖：`G-202`、`G-205`
- 完成标准：研究记录不会冒充真相层，入口路径也不会绕远

### D. 证据编目与命名纪律

#### G-301：建立 retained artifact manifest

- 要做什么：给保留的 run 和代表性 artifact 建立轻量 manifest / index
- 依赖：`G-105`
- 完成标准：保留下来的证据都有登记入口，不再允许“先留着再说”

#### G-302：统一 manual run 命名与标签

- 要做什么：固定 manual run 的命名规范和标签字段
- 依赖：`G-301`
- 完成标准：同类 run 的命名和筛选方式稳定可复用

#### G-303：建立代表性 run 白名单

- 要做什么：明确哪些 runs 是代表性保留对象，哪些不是
- 依赖：`G-301`
- 完成标准：保留集合有显式边界，不再靠个人印象

#### G-304：补 retention metadata

- 要做什么：为 retained artifact 补“为什么保留、保留级别、下次复查时间”
- 依赖：`G-303`
- 完成标准：保留下来的证据以后仍然可解释、可复查

### E. 收口检查与验收门

#### G-401：脚本化 closeout gate

- 要做什么：把 closeout 退出条件变成脚本化检查
- 依赖：`G-106`、`G-206`、`G-304`
- 完成标准：收口状态能被重复验证，而不是靠主观判断

#### G-402：检查残留运行态与 deploy sync

- 要做什么：让 gate 检查 `active round`、`candidate worktree`、未完成 cleanup 和 deploy sync verify
- 依赖：`G-401`
- 完成标准：不会在“看起来已收口”时把半拉子运行态带进下一阶段

#### G-403：落盘 gate 结果与 readable summary

- 要做什么：把 gate 结果写成正式记录，并输出一份可读 summary
- 依赖：`G-402`
- 完成标准：验收结果能 handoff、能复盘、能回查

## 三、最小里程碑

### Milestone 1：Freeze

- 包含任务：`G-001`、`G-002`、`G-003`
- 达标判断：收口边界与 authority 已冻结

### Milestone 2：Retention Baseline

- 包含任务：`G-101`、`G-102`、`G-103`、`G-104`
- 达标判断：artifact 留删规则和日志规则已成形

### Milestone 3：Dry Cleanup

- 包含任务：`G-105`、`G-106`
- 达标判断：规则已被实际执行并固化进 runbook

### Milestone 4：Closeout Surface

- 包含任务：`G-201`、`G-202`、`G-203`、`G-204`、`G-205`、`G-206`
- 达标判断：当前入口清楚、历史入口退场、closeout 主入口稳定

### Milestone 5：Evidence Catalog

- 包含任务：`G-301`、`G-302`、`G-303`、`G-304`
- 达标判断：保留证据有 manifest、命名规则和保留解释

### Milestone 6：Gate

- 包含任务：`G-401`、`G-402`、`G-403`
- 达标判断：closeout gate 能正式证明当前阶段已可信收口

## 四、明确不纳入本清单

- 下一阶段 implementation task plan
- P2 问题审计、低分 taxonomy、瓶颈排序
- `feedback contract`、`mutation`、prompt 改写和其他开发准备
- 下一阶段 canary 和验证体系重构

## 五、相关文档

- [Autoresearch：收口治理目标](./autoresearch-closeout-governance-goals.md)
- [Autoresearch P2：TMP Exrepo 运行时迁移与维护脚本任务规划](./autoresearch-p2-tmp-exrepo-runtime-task-plan.md)
- [Analysis README](./README.md)
