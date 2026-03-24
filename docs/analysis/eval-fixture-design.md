---
title: "Repo-local 测试仓库与问题列表设计"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Repo-local 测试仓库与问题列表设计

> 目的：把当前仓库怎么选测试仓库、怎么设计关键问题列表、怎么保存测试记录和测试评分说清楚，作为 prompt 改进流程的补充说明。

## 一、这页回答什么

本页只回答 4 个问题：

- 测试仓库应该怎么选
- 关键问题应该怎么列
- 测试记录应该记什么
- 测试评分应该看什么

本页不负责回答：

- prompt 的真相定义写在哪里
- 业务源码该怎么组织
- 是否要搭一个更大的评测平台

## 二、测试仓库怎么选

当前更适合用“少量、稳定、能重复”的测试仓库，而不是一次铺很多。

更稳的选择标准是：

1. 能固定到某个 commit
2. 有清晰入口，最好是 `CLI` 或强文本流仓库
3. setup 成本低
4. 测试仓库本身不要太大
5. 结构和模块边界相对清楚

这样做的目的不是凑数据集，而是让同一组问题能在不同轮次里被稳定复跑。

## 三、关键问题怎么列

关键问题列表应直接服务 prompt 改进，而不是为了把题库做大。

当前更适合的问题类型是：

- 入口判断题
  - AI 能不能先读对文档入口和代码入口
- 边界判断题
  - AI 会不会把不该读的层当成主线
- 覆盖判断题
  - 回答有没有覆盖应该回答的关键点
- 表达判断题
  - 回答是不是清楚、克制、没有跑偏

如果问题很多，但看不出它们和 prompt 改进的关系，这组问题就不够好。

## 四、测试记录应该记什么

测试记录不需要写得很花，只要足够复盘即可。

至少要记录：

- 测试仓库
- backend
- 当前 prompt / wrapper 版本
- 问题内容
- 原始回答
- 运行时间
- 输出路径

这些信息的作用只是让你知道“这一轮 prompt 回答成了什么样”，不是为了制造更多格式对象。

## 五、测试评分看什么

测试评分当前更适合看下面几类最直接的指标：

- 是否答到了关键点
- 是否有明显错误
- 是否有无关展开
- 是否越过了路径边界
- `Codex` 和 `Claude` 的表现差异有多大

如果需要更细一点，也应优先围绕“回答质量”而不是“格式完整性”展开。

## 六、当前推荐的最小落点

当前推荐的最小落点是：

- `docs/analysis/`
  - 保存测试方法和问题设计说明
- `toolchain/evals/fixtures/`
  - 保存测试仓库说明格式和测试记录格式
- `toolchain/evals/*/`
  - 保存具体主题的问题列表和测试评分规则
- `.autoworkflow/`
  - 保存实际测试记录

## 七、当前不应把重点放在哪里

按现在仓库状态，下面这些都不应该抢走主流程：

- 不先把测试格式写得越来越复杂
- 不先扩一大批测试仓库
- 不先把目录分得越来越细
- 不先让 schema 和术语变成主角

真正的主流程仍然只有一句话：

在同一个测试仓库里，用同一组关键问题比较 `Codex` 和 `Claude` 的 prompt 表现，并据此继续改 prompt。

## 八、相关文档

- [Repo-local Prompt 测试与改进流程](./eval-method-evolution.md)
- [Memory Side Repo-local Prompt 改进闭环](./memory-side/memory-side-auto-research-loop.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side/memory-side-eval-baseline.md)
- [Task Interface Repo-local Adapter 评测基线](./task-interface/task-interface-eval-baseline.md)
