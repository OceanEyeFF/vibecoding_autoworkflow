---
title: "Repo-local Eval 研究推进步骤"
status: active
updated: 2026-03-24
owner: aw-kernel
last_verified: 2026-03-24
---
# Repo-local Eval 研究推进步骤

> 目的：把当前仓库评测方法后续怎么继续推进写清楚，但只作为研究推进顺序和边界说明，不把它写成已经承诺落地的大方案。

## 一、当前判断

当前仓库已经有一条最小可运行的 `Memory Side` 评测线：

- `toolchain/evals/memory-side/` 提供稳定测量面
- `toolchain/scripts/research/memory_side_autoresearch.py` 提供最小 runner
- `codex` 与 `claude` CLI 都已经接进当前 runner

但这条线还只是单主题、最小闭环。

`Task Interface` 目前还没有独立的程序化测量面，因此不适合直接把下一步定义成“统一成一个大而全的通用 eval 平台”。

## 二、当前方法来源

后续研究可以参考两类来源，但要分层使用：

1. `karpathy/autoresearch`
   - 主要借它的研究方法
   - 核心是固定 `program`、固定场景、固定 schema 或机械指标、重复试验、统一比较
2. `uditgoenka/autoresearch`
   - 主要借它的 Claude 侧执行壳、loop、guard、logging 思路
   - 不直接把整套命令面、插件体系和大 catalog 作为本仓库主线

这里的重点不是“照搬外部仓库”，而是把其中可复用的方法压进本仓库现有分层里。

## 三、固定边界

在继续推进研究方法时，下面这些边界不能漂移：

- `docs/knowledge/` 仍然是真相层，不是实验层
- `product/` 仍然是 canonical skill 与 adapter 源码层
- `toolchain/evals/` 仍然只保存稳定测量面
- `toolchain/scripts/research/` 仍然只保存研究执行与评分入口
- `.agents/` 与 `.claude/` 仍然只是 deploy target
- `.autoworkflow/` 仍然只是运行产物目录

因此，评测方法的演进只能先从 `analysis`、`evals`、`scripts/research` 和 adapter 实现层推进，不能反过来改写真相层定义。

## 四、推进原则

后续完善评测时，优先遵守下面几条：

1. 先补稳定测量面，再补更复杂的执行后端
2. 先做单主题收口，再做跨主题抽象
3. 先做人工可复核的机械检查，再做自动化扩展
4. 先测 repo-local adapter，再考虑单独测 canonical skill
5. 每一步都要能回答“如果今天停在这里，是否仍然自洽”

如果某一步必须先引入抽象层、统一 runner、额外 backend 或复杂 loop 才能开始，通常说明步子迈大了。

## 五、建议推进顺序

### Step 1. 先把当前 `Memory Side` 评测线压实

这一阶段不新增新主题，不引入新宿主，只做下面几件事：

- 保持 `program.md`、`scenarios.json`、`schemas/`、`scoring/` 的稳定性
- 继续用当前 `codex` / `claude` 命令级 runner 跑固定场景
- 让评分和运行记录更容易人工复核
- 确认 dry run、真实运行、评分三段链路都稳定

这一阶段的完成标志：

- 当前场景集不再频繁改 schema
- 两个 backend 至少能在同一组场景下重复出结果
- 评分结论可以稳定复现

### Step 2. 再给 `Task Interface` 补最小测量面

这一阶段不急着写通用 runner，先把缺的资产补齐：

- `toolchain/evals/task-interface/`
- 最小 `Task Contract` 输出 schema
- 最小场景集
- 对 `confirmed / pending` 边界的 rubric

这一阶段的目标不是“做大”，而是让 `Task Interface` 从人工基线进入最小程序化验证。

这一阶段的完成标志：

- `Task Interface` 也具备和 `Memory Side` 类似的最小测量面
- 输出能被固定 schema 检查
- 人工验收开始有程序化辅助，而不是完全手工判断

### Step 3. 等两个主题都稳定后，再抽共享 runner

只有当 `Memory Side` 和 `Task Interface` 都已经有独立测量面时，才值得做共享抽象。

这时再考虑把当前 runner 抽成：

- 主题参数化
- backend 参数化
- 通用 manifest 结构
- 通用评分入口

在这一步之前，不必急着把现有脚本重构成“大一统框架”。

### Step 4. 把 Claude 侧扩展保持在 backend 层

如果后续要继续参考 `uditgoenka/autoresearch`，优先吸收的是：

- loop 约束
- guard 思路
- logging 结构
- 更稳定的 Claude 非交互调用方式

不建议在当前仓库直接引入：

- 大量 `/autoresearch:*` 子命令
- 面向通用业务域的 command catalog
- 把本仓库误写成 Claude 插件宿主系统的结构

这一阶段的目标只是让 `Claude` backend 更稳，不是把仓库改造成另一个 `autoresearch` 产品。

### Step 5. 最后才引入 OpenAI API 侧验证

OpenAI API 可以进入评测面，但建议放在更后面，而且边界要写死：

- 它更适合用来测 canonical skill contract 的稳定输出
- 它不等于本仓库又多了一个 repo-local skill host
- 它不应该先于 `Task Interface` 测量面补齐
- 它不应该先于共享 schema 和评分规则稳定下来

更具体地说：

- `codex` / `claude` CLI 主要测 repo-local adapter 与 deploy target
- OpenAI API 更适合单独测“在固定 prompt + 固定 schema 下，canonical contract 是否稳定”

只有当这个边界被写清楚，OpenAI API 的引入才不会把 adapter eval 和 canonical skill eval 混在一起。

## 六、当前阶段明确不做什么

按现在仓库状态，下面这些都不应当成为近期默认动作：

- 不直接把当前脚本重构成跨主题大平台
- 不默认引入无限 loop、自动提交、自动回滚
- 不为了接 OpenAI API 先抽象出过度设计的 backend framework
- 不把外部 `autoresearch` 仓库的命令树照搬进来
- 不在没有稳定 schema 的情况下比较不同 backend 的优劣

## 七、一个更稳的近期落点

如果只看近期最务实的推进，建议顺序是：

1. 把这套研究方法先写进 `docs/analysis/`
2. 继续用当前 `Memory Side` runner 做少量固定场景复跑
3. 补 `Task Interface` 的最小 schema、场景和 rubric
4. 再决定是否值得抽共享 runner

这样做的好处是：

- 每一步都能停住
- 每一步都能复核
- 每一步都不会把仓库往宿主工作流系统方向推偏

## 八、外部参考

- `karpathy/autoresearch`
  - <https://github.com/karpathy/autoresearch>
- `uditgoenka/autoresearch`
  - <https://github.com/uditgoenka/autoresearch>

## 九、相关文档

- [Analysis README](./README.md)
- [Memory Side Repo-local Auto Research Loop](./memory-side/memory-side-auto-research-loop.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side/memory-side-eval-baseline.md)
- [Task Interface Repo-local Adapter 评测基线](./task-interface/task-interface-eval-baseline.md)
