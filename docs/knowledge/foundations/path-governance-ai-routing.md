---
title: "路径治理与 AI 告知"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# 路径治理与 AI 告知

> 目的：把当前仓库的“目录排布规则”和“AI 进入仓库时该怎么读路径”固化成同一份 foundations 合同，避免主线入口、隐藏层、兼容层和局部入口继续各说各话。

## 一、适用范围

本合同只回答两件事：

- 当前仓库的正式内容区和非正式内容区分别是什么
- AI 进入仓库时，默认先读什么、后读什么、先不要读什么

它不是执行计划，也不是某个后端专属 prompt。

## 二、根目录合同

当前仓库根目录只有三块正式内容区：

1. `product/`
2. `docs/`
3. `toolchain/`

除此之外，其余根目录对象默认都不是主线真相层：

- `.agents/`、`.claude/`、`.opencode/`：repo-local mount / deploy target
- `.autoworkflow/`、`.spec-workflow/`：repo-local state
- `.serena/`：repo-local state/config，可保留受控入库的项目级配置与记忆
- `.nav/`：compatibility navigation
- `README.md`、`INDEX.md`、`GUIDE.md`、`ROADMAP.md`、`AGENTS.md`：Entry Layer
- `.git*`：Repo Infra

## 三、根级 Route Contract

### `read_first`

1. `docs/README.md`
2. `docs/knowledge/README.md`
3. `docs/knowledge/foundations/README.md`
4. `docs/knowledge/foundations/root-directory-layering.md`
5. `docs/knowledge/foundations/path-governance-ai-routing.md`
6. `docs/knowledge/foundations/docs-governance.md`
7. `docs/knowledge/foundations/toolchain-layering.md`
8. `docs/knowledge/memory-side/layer-boundary.md`

### `read_next`

- `docs/knowledge/memory-side/overview.md`
- `docs/knowledge/memory-side/skill-agent-model.md`
- `docs/knowledge/task-interface/task-contract.md`
- 按任务进入 `product/`、`docs/` 或 `toolchain/` 的局部入口页

### `do_not_read_yet`

- `.agents/`
- `.claude/`
- `.opencode/`
- `.autoworkflow/`
- `.spec-workflow/`
- `.serena/`
- `.nav/`
- `docs/reference/`
- `docs/ideas/`
- `docs/archive/`

### `stop_reading_when`

- 已确认当前任务落在哪一块正式内容区
- 已拿到当前任务所需的最小模块入口
- 继续扩读只会重复背景，而不会增加决策价值

## 四、三块正式内容区的最小读取合同

### 1. `product/`

职责：

- 业务代码唯一源码根
- canonical skill 与 backend adapter 的 source of truth

`read_first`

1. `product/README.md`
2. `product/memory-side/README.md` 或 `product/task-interface/README.md`
3. 对应 partition 的 `skills/README.md` 或 `adapters/README.md`

`read_next`

- 目标 skill 的 `SKILL.md`
- 对应 backend wrapper

`do_not_read_yet`

- 根目录 `.agents/`
- 根目录 `.claude/`
- 根目录 `.opencode/`
- `docs/operations/`
- `toolchain/evals/`

`stop_reading_when`

- 已确认当前源码入口
- 已确认当前任务涉及哪个 partition、哪个 canonical skill 或哪个 backend adapter

### 2. `docs/`

职责：

- 仓库真相、基础治理、repo-local 运行说明、研究说明和参考分层

`read_first`

1. `docs/README.md`
2. `docs/knowledge/README.md`
3. `docs/knowledge/foundations/README.md`
4. `docs/knowledge/foundations/root-directory-layering.md`
5. `docs/knowledge/foundations/path-governance-ai-routing.md`
6. `docs/knowledge/foundations/docs-governance.md`
7. 目标领域的 `knowledge/` 主线文档

`read_next`

- 需要部署或维护时进入 `docs/operations/README.md`
- 只有任务明确要求历史研究或新准入研究时，才进入 `docs/analysis/README.md`

`do_not_read_yet`

- `docs/reference/`
- `docs/ideas/`
- `docs/archive/`

`stop_reading_when`

- 已确认当前文档落点属于 `knowledge / operations / analysis / reference / ideas / archive` 的哪一层
- 已拿到可直接开始编辑或判断的目标文档

### 3. `toolchain/`

职责：

- 脚本、评测、测试、打包、部署工具

`read_first`

1. `toolchain/README.md`
2. `toolchain/scripts/README.md` 或 `toolchain/evals/README.md`
3. 目标二级入口，例如 `scripts/deploy/README.md`、`scripts/test/README.md`

`read_next`

- 目标 CLI 脚本
- 目标治理说明
- 只有任务明确要求测量资产时，才继续进入 `scripts/research/` 或 `evals/`

`do_not_read_yet`

- `product/` 下的业务源码
- `.autoworkflow/` 下的运行产物
- `.agents/`、`.claude/` 与 `.opencode/`

`stop_reading_when`

- 已确认当前任务属于部署、评测、测试还是打包
- 已定位到最小工具入口

## 五、隐藏层和兼容层的默认定位

### 1. `.agents/`、`.claude/` 与 `.opencode/`

- 这是 repo-local deploy target
- 不是业务源码层
- 不是项目真相层
- 默认不进入

### 2. `.autoworkflow/`、`.spec-workflow/`、`.serena/`

- 这是 repo-local state/config
- `.autoworkflow/` 与 `.spec-workflow/` 承载运行结果、审批状态和工具状态
- `.serena/` 可保留受控入库的项目级配置与记忆，但不属于主线真相层
- 默认不进入，只有任务明确要求读取运行结果、审批状态或 Serena 项目配置时才进入

### 3. `.nav/`

- 这是 compatibility navigation
- 只服务兼容跳转，不服务结构定义
- 默认不作为 AI 的执行入口

## 六、什么时候允许扩读到次级文档层

### 1. 进入 `docs/operations/`

只在下面情况进入：

- 任务明确涉及 repo-local 部署
- 任务明确涉及维护步骤、运行手册或 adapter 使用帮助

### 2. 进入 `docs/analysis/`

只在下面情况进入：

- 任务明确涉及已准入研究说明
- 任务明确要求查看历史分析结论

### 3. 进入 `docs/reference/`

只在下面情况进入：

- 主线文档不足以支持判断
- 明确需要外部方法论或引文背景

### 4. 进入 `docs/ideas/` 与 `docs/archive/`

只在下面情况进入：

- 任务明确需要探索候选方案
- 任务明确需要追溯历史或归档脉络

默认不把这两层当执行基线。

## 七、失败信号

如果出现下面任一现象，说明 AI 路径治理又开始失效：

- AI 一开始就进入 `.agents/`、`.claude/`、`.opencode/` 或 `.nav/`
- AI 跳过 `docs/README.md` 和 foundations 主线文档直接全仓扫描
- `docs/reference/`、`docs/ideas/`、`docs/archive/` 被默认当成执行基线
- repo-local state 被误当成项目真相
- 三块正式内容区以外的目录重新被写成“主线入口”

## 八、相关文档

- [根目录分层](./root-directory-layering.md)
- [Toolchain 分层](./toolchain-layering.md)
- [Docs 模块入口](../../README.md)
- [Memory Side 层级边界](../memory-side/layer-boundary.md)
- [Context Routing 分流规则](../memory-side/context-routing-rules.md)
