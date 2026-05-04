---
title: "Existing Code Project Adoption"
status: active
updated: 2026-04-25
owner: aw-kernel
last_verified: 2026-04-25
---
# Existing Code Project Adoption

> 目的：定义把一个已有代码库接入 Harness 时，`.aw/repo/discovery-input.md` 如何作为只读事实输入进入初始化流程。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Template Consumption Spec](./template-consumption-spec.md)
- [Template Tooling MVP](./template-tooling-mvp.md)
- [Harness Artifact / Repo](../../harness/artifact/repo/README.md)

## 一、范围

Existing Code Project Adoption 用于目标 repo 已经存在代码、文档、脚本或治理规则，但尚未建立 Harness `.aw/` 控制面，或尚未把既有事实接入 `set-harness-goal-skill` 初始化流程的场景。

本模式新增的 artifact/template 支持是：

- canonical artifact definition：`docs/harness/artifact/repo/discovery-input.md`
- skill-owned template source：`product/harness/skills/set-harness-goal-skill/assets/repo/discovery-input.md`
- runtime target：`.aw/repo/discovery-input.md`

当前脚本集成已落在 `product/harness/skills/set-harness-goal-skill/scripts/deploy_aw.js`：`generate --adoption-mode existing-code-adoption` 在默认/profile 生成时会从 `assets/repo/discovery-input.md` 渲染 `.aw/repo/discovery-input.md`。本页不展开内部实现细节，只定义 operator-facing 生成边界、artifact authority，以及 discovery 与 goal / snapshot / control 的关系；该行为应由 `toolchain/scripts/test/test_set_harness_goal_deploy_aw_node.py` 覆盖。

## 二、核心语义

`.aw/repo/discovery-input.md` 是只读事实输入，不是 goal truth。

它记录的是 adoption 前后从已有代码库观察到的事实和不确定点，例如：

- 目录、模块、入口、语言栈和构建系统线索
- 测试、运行、部署或发布脚本线索
- 现有文档、agent 指令、分层规则和治理说明
- 当前分支、提交、未提交变更和风险
- 可追溯的候选目标信号
- 需要用户确认的问题

它不能记录成：

- 用户已经确认的长期目标
- Harness 控制指令
- worktrack 拆分方案
- 对既有实现意图的不可追溯推断
- 覆盖用户目标的依据

## 三、生成关系

当前脚本层接入本模式后的生成关系为：

| source | target | 说明 |
|---|---|---|
| `assets/repo/discovery-input.md` | `.aw/repo/discovery-input.md` | Existing Code Project Adoption 的只读事实输入 |
| `assets/goal-charter.md` | `.aw/goal-charter.md` | 用户确认后的长期目标 truth |
| `assets/repo/analysis.md` | `.aw/repo/analysis.md` | RepoScope 阶段性分析与优先级判断 |
| `assets/repo/snapshot-status.md` | `.aw/repo/snapshot-status.md` | 初始化后的 repo 慢变量状态 |
| `assets/control-state.md` | `.aw/control-state.md` | Harness supervisor 当前控制状态 |

`discovery-input.md` 可以先生成，也可以和其他 `.aw/` 初始化文件同轮生成；无论实现顺序如何，它都不能绕过 `goal-charter.md` 的用户确认边界。`repo/analysis.md` 可以引用 discovery 的事实线索做阶段性判断，但它仍是决策支撑 artifact，不是目标真相。

## 四、与 `goal-charter.md` 的关系

`discovery-input.md` 可以向 `goal-charter.md` 提供候选目标信号，但不能成为目标本身。

正确流程是：

- 从既有 repo 采集事实和候选信号
- 把候选信号展示给用户确认
- 只把确认后的长期目标、成功标准、系统不变量写入 `.aw/goal-charter.md`

如果用户确认结果和 discovery 候选信号不一致，以 `.aw/goal-charter.md` 为准。

## 五、与 `repo/snapshot-status.md` 的关系

`discovery-input.md` 是初始化事实输入；`repo/snapshot-status.md` 是初始化后的慢变量观测面。

因此：

- snapshot 可以引用 discovery 中的事实来源
- snapshot 应归纳当前 repo 状态，而不是复制 discovery 原文
- 后续 repo refresh 应更新 snapshot，不应回写 discovery 作为长期状态
- 如果后续观测发现 discovery 过期或错误，以刷新后的 snapshot 为准

## 六、与 `control-state.md` 的关系

`control-state.md` 只保存 supervisor 当前状态，不保存业务事实。

在 adoption 模式下，control state 可以：

- 在 `Linked Formal Documents` 或 `Notes` 中链接 `.aw/repo/discovery-input.md`
- 记录当前已进入 `repo_scope: active`、`worktrack_scope: closed`
- 继续使用保守的初始 autonomy 设置

control state 不应该：

- 复制 discovery 的 repo inventory
- 把 discovery 的候选目标写成控制指令
- 用 discovery 绕过 handback / approval / goal confirmation

## 七、当前脚本集成边界

当前 `deploy_aw.js` 集成必须保持下面边界：

- operator-facing 参数为 `generate --adoption-mode existing-code-adoption`；默认/profile 生成会自动包含 `repo-discovery-input`，显式 `--template` 选择仍以调用方选择为准
- 生成目标固定为 `.aw/repo/discovery-input.md`
- 该文件应来自 `set-harness-goal-skill` 自带 `assets/repo/discovery-input.md`
- baseline branch 必须来自显式 `--baseline-branch` / `AW_BASELINE_BRANCH`，或来自 `origin/HEAD`、唯一 `origin/main|origin/master`、唯一 local `main|master` 等可验证 ref；不能退回到 `init.defaultBranch` 或写死 `main`
- 不覆盖已有 `.aw/goal-charter.md`
- 不把 adoption 模式写成 deploy target 安装行为
- 不让 adapter payload source 成为 artifact truth

当前 canonical truth 仍由 `docs/harness/artifact/repo/discovery-input.md` 承接；可执行模板仍由 `product/harness/skills/set-harness-goal-skill/assets/repo/discovery-input.md` 承接。

## 八、验收标准

本模式文档与模板支持可认为达标，当下面几项成立：

- repo artifact 入口列出 `discovery-input.md`
- set-harness-goal skill assets 入口列出 `repo/discovery-input.md`
- skill workflow 明确 existing-code-adoption 先采集只读事实输入
- deploy 文档明确 `.aw/repo/discovery-input.md` 不是 goal truth
- deploy 文档明确 discovery 与 snapshot / goal / control 的关系
- `deploy_aw.js` 已支持 `--adoption-mode existing-code-adoption`，并有测试覆盖默认/profile 生成 `.aw/repo/discovery-input.md`
- `deploy_aw.js` 在 baseline branch 不可验证时会阻断生成，要求显式传入或提供可验证 ref
