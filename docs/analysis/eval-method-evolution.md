---
title: "Repo-local Prompt 测试与改进流程"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Repo-local Prompt 测试与改进流程

> 目的：把当前仓库怎么用本地测试仓库、同一组关键问题和简单评分，来持续改进 `Codex` 与 `Claude` 的 prompt 说明清楚，不把它写成一个大而全的评测平台。

## 一、当前主目标

当前主目标不是把“评测体系”越做越大，而是把下面这件事稳定下来：

- 给 `Codex` 和 `Claude` 部署各自的 prompt / wrapper
- 在同一个测试仓库里跑同一组关键问题
- 保存测试记录
- 做简单、稳定的测试评分
- 根据结果继续改 prompt

所以，当前真正的被测试对象是：

- `docs/knowledge/` 里的 adapter prompt 文案
- `product/` 下给 `Codex` / `Claude` 的 adapter wrapper
- 必要时的基础测试提示，例如 `toolchain/evals/*/program.md`

不是：

- `docs/knowledge/` 的真相正文
- `.agents/` 或 `.claude/` 里的部署结果
- 一个越来越复杂的评测平台

## 二、最小测试流程

当前更适合坚持下面这 5 步：

1. 固定一个本地测试仓库
2. 固定一组关键问题
3. 给 `Codex` 与 `Claude` 部署各自的 prompt / wrapper
4. 用无交互模式分别跑同一组问题
5. 保存测试记录并评分，然后只改 prompt 再重跑

如果一轮工作不能清楚回答下面 3 个问题，通常说明流程又写偏了：

- 这轮到底改了哪段 prompt 或 wrapper
- 这轮用了哪组关键问题来验证
- 跑完之后，什么结果会让我们保留或回退这次修改

## 三、固定不动的东西

为了让 prompt 迭代有对比意义，下面这些东西应尽量固定：

- 测试仓库
- 问题列表
- 测试记录格式
- 测试评分规则

它们的作用只是让不同轮次的 prompt 输出可以直接比较，不是为了反过来主导整个项目。

## 四、需要不断调整的东西

当前真正需要不断调整的，是下面这些对象：

- `Codex` prompt
- `Claude` prompt
- 很薄的一层 backend wrapper

如果一轮工作主要在增加 schema、目录、格式层，而不是帮助 prompt 更快变好，这轮工作大概率就偏成了“为了评测而评测”。

## 五、当前优先顺序

当前更稳的顺序是：

1. 先把 `Memory Side` 这条线跑顺
2. 先把同一组关键问题在 `Codex` 与 `Claude` 上稳定复跑
3. 先让测试记录和测试评分足够稳定、足够容易人工复核
4. 再考虑是否扩到更多测试仓库或更多主题

只有在这条最小闭环已经稳定后，才值得继续补更复杂的测试结构。

## 六、当前不应优先做什么

按现在仓库状态，下面这些都不应当成为当前主目标：

- 不先把评测写成大平台路线图
- 不先为了格式完整去扩大量 schema、manifest 和术语
- 不先铺很多测试仓库
- 不先扩很多 backend
- 不先把“自动研究”写成复杂 loop

如果这些东西开始比“prompt 改没改好”更显眼，就说明文档口径又偏了。

## 七、当前文档和目录各自负责什么

- `docs/analysis/`
  - 解释测试怎么服务 prompt 改进
- `toolchain/evals/`
  - 保存问题列表、测试记录格式和测试评分规则
- `toolchain/scripts/research/`
  - 保存执行测试和计算分数的脚本
- `.autoworkflow/`
  - 保存实际测试记录和运行结果

## 八、相关文档

- [Analysis README](./README.md)
- [Repo-local 测试仓库与问题列表设计](./eval-fixture-design.md)
- [Memory Side Repo-local Prompt 改进闭环](./memory-side/memory-side-auto-research-loop.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side/memory-side-eval-baseline.md)
- [Task Interface Repo-local Adapter 评测基线](./task-interface/task-interface-eval-baseline.md)
