---
title: "Repo-local Eval 基底 Repo 与任务模板设计"
status: active
updated: 2026-03-24
owner: aw-kernel
last_verified: 2026-03-24
---
# Repo-local Eval 基底 Repo 与任务模板设计

> 目的：把 `repo fixture`、任务模板、数据集来源和细节资产单独落成一页，作为 [Repo-local Eval 研究推进步骤](./eval-method-evolution.md) 的重内容补充，而不把路线文档压得过重。

## 一、定位

本页不负责定义推进阶段，也不承诺当前仓库已经实现下列资产。

本页只回答 4 个问题：

- 评测用的基底 repo 应该怎么选
- 任务模板应该怎么拆
- 数据集应从哪里来
- 后续更细的评测资产应落到哪里

路线、边界和先后顺序，仍以：

- [Repo-local Eval 研究推进步骤](./eval-method-evolution.md)

为主。

## 二、默认假设：`CLI-first`

当前评测设计默认优先覆盖 `CLI / text-stream` 场景，而不是先覆盖 GUI 或复杂交互式宿主。

原因：

- 当前主要执行入口本来就是 `Codex CLI`、`Claude CLI` 和 `OpenAI API`
- `CLI` 场景更容易固定输入输出边界
- `CLI` repo 更适合做自动 gate、自动 judge 和回归比较
- 文本流更接近当前仓库要约束的真实交互形态

这不意味着后续永远不测其他场景，而是意味着第一波基底 repo 应优先满足：

- 有清晰命令入口
- 有明确文本输出
- 有稳定测试
- setup 成本低
- token 成本可控

## 三、基底 Repo 选择原则

第一阶段不需要“很多 repo”，而需要“少量、稳定、可重复”的 repo fixtures。

更合适的约束是：

1. 每种语言先选 `1-2` 个 repo
2. 优先选 `CLI-first` 或强文本流 repo
3. 优先选小而真实、可在单次评测中吃下的代码库
4. 必须能固定到 commit，避免上游漂移
5. 必须有清晰测试入口
6. 优先选结构清楚、模块边界明显的项目
7. 不优先选需要大量 GUI、浏览器或复杂服务依赖的项目

## 四、当前更合适的初始候选

下面这些更适合做第一波候选，但当前仍应视为“建议 shortlist”，不是已经正式准入的 benchmark 资产。

### Python

- `fastapi/typer`
  - 适合测 `CLI` 参数、命令组织、帮助文本、文档与代码一致性
- `httpie/cli`
  - 适合测更真实的长期维护任务、参数变更和行为更新

### TypeScript

- `tj/commander.js`
  - 适合测典型 `CLI` 参数解析、命令结构和 API 记忆
- `oclif/core`
  - 适合测更强的子命令组织和较复杂的 `CLI` 结构

### C++

- `CLIUtils/CLI11`
  - 适合做跨语言 `CLI` 对比，也适合测参数系统和帮助文本
- `fmtlib/fmt`
  - 更偏文本输出与格式规则，适合补强 `CLI` 文本生成相关场景

### Prompt / Text-only

`Prompt` 不应先被视为一种语言 repo，而更适合作为独立任务族：

- 讨论收束成 `Task Contract`
- 任务开始前的 `Context Routing`
- 任务结束后的 `Writeback` 与 mismatch 处理

## 五、任务模板

当前更适合先固定 5 类任务模板。

### 1. 事实写入

目标：

- 从 repo 与任务上下文中提取稳定事实
- 输出结构化结果
- 不改代码

更接近：

- `Knowledge Base`
- `Writeback & Cleanup`

### 2. 基于记忆的读取与引用

目标：

- 优先消费已有记忆或入口
- 避免重复盲读
- 引用已有上下文而不是幻觉补全

更接近：

- `Knowledge Base`
- `Context Routing`

### 3. mismatch 更新

目标：

- 找到现有记忆与最新事实的冲突
- 更新结果并保留边界
- 不把旧事实静默覆盖成新事实

更接近：

- `Writeback & Cleanup`

### 4. 任务收束与优化

目标：

- 把模糊讨论收束成稳定任务基线
- 明确范围、非目标、依赖、风险和验收
- 控制上下文膨胀

更接近：

- `Task Contract`

### 5. 长链 continuation

目标：

- 让同一任务跨多个步骤保持一致
- 在写入、修改、更新、再收束之间不漂移
- 暴露长期上下文管理问题

这类任务不应作为最初 hard gate，而更适合在自动 judge 已经稳定后成为强压力场景。

## 六、数据集来源

后续数据集不应只来自单一来源，而应至少分成 4 类：

1. 种子场景
   - 当前仓库已有的最小 benchmark 场景
   - 适合做第一波自动运行
2. 外部基底 repo fixtures
   - 以固定 commit 的外部 repo 作为标准材料
   - 适合做跨语言、跨结构对比
3. 合成变更样本
   - 人工或脚本注入的小范围改动、冲突和 mismatch
   - 适合测更新和回写边界
4. 真实失败日志
   - 来自双后端运行中的高频失败、分歧和漂移案例
   - 适合在后期沉淀为正式评测集

当前更稳的顺序仍然是：

- 先用种子场景和少量外部 fixture 起跑
- 再从真实失败日志反推正式评测集

## 七、细节资产建议

如果后续把这套东西继续压实，建议把稳定资产拆成下面几类。

### 1. fixture manifest

建议记录：

- repo 标识
- 固定 commit
- 语言
- setup 命令
- test 命令
- CLI 入口
- 禁读或禁改路径
- 适用任务族

### 2. task template

建议记录：

- task id
- 任务族
- 输入材料
- 允许动作
- 禁止动作
- 期望输出结构
- judge 入口

### 3. judge schema 与 rubric

建议记录：

- 结构合法性
- 事实正确性
- 冗余率
- 漂移率
- 范围控制
- `pass / fail / inconclusive` 判定条件

### 4. run manifest

建议记录：

- backend
- model
- scenario id
- fixture id
- token 或调用成本
- 读文件数
- 运行轮数
- 输出路径
- 最终判定

## 八、建议的落点

稳定说明和研究记录继续放在：

- `docs/analysis/`

稳定测量资产后续应优先落到：

```text
toolchain/evals/
```

运行产物仍应落到：

```text
.autoworkflow/
```

如果后续加入 fixture manifest，更适合放在：

```text
toolchain/evals/fixtures/
```

而不是单独新起一个根级 benchmark 仓结构。

## 九、相关文档

- [Repo-local Eval 研究推进步骤](./eval-method-evolution.md)
- [Memory Side Repo-local Auto Research Loop](./memory-side/memory-side-auto-research-loop.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side/memory-side-eval-baseline.md)
- [Task Interface Repo-local Adapter 评测基线](./task-interface/task-interface-eval-baseline.md)
