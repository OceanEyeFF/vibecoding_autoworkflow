---
title: "Knowledge Base 适配 Prompt 草案"
status: draft
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Knowledge Base 适配 Prompt 草案

> 目的：作为 `Claude`、`Codex`、`OpenCode`、`OpenClaw` 等后端可复用的通用 Prompt contract，指导 AI 建立、接管和维护目标仓库里的 `Knowledge Base`。

## 一、适用场景

- 仓库缺少文档体系，需要建立最小 `Knowledge Base`
- 仓库已有文档体系，需要扫描、识别和接管
- 任务完成后，需要把确认过的项目真相回写到合适的文档层级

## 二、核心原则

- 仓库内静态文档是真相本体
- Prompt 只是维护层，不是真相层
- 不要为某个后端维护私有项目真相
- 不要把 `ideas / discussions / thinking` 直接当执行基线
- 不要把 `archive` 当默认阅读入口

## 三、工作模式

### 1. Bootstrap Mode

当仓库没有成型文档体系时：

- 建立最小入口文档
- 建立 `Core Truth` 的基本骨架
- 只补必要结构，不追求一次写全

### 2. Adopt Mode

当仓库已有文档体系时：

- 先扫描现有文档
- 识别 `Core Truth`、`Operational Truth`、`Exploratory Records`、`Archive`
- 先补索引、状态和链接，再考虑重写

## 四、执行步骤

1. 先确认仓库当前有哪些文档和入口。
2. 判断当前更接近 `Bootstrap Mode` 还是 `Adopt Mode`。
3. 识别文档分层，不要把所有文档当成同一可信级别。
4. 如果缺失主线入口，优先补主线入口。
5. 如果已有体系，优先补文档地图和状态字段。
6. 修改文档时，优先维护主线真相，不扩大无关范围。

## 五、硬性约束

- 没有读取文档前，不要声称知道项目文档体系
- 没有确认状态前，不要把某份文档当成当前真相
- 不要因为发现旧文档就默认全部重写
- 不要把探索文档内容自动提升为主线规则
- 不要把仓库外对话内容写成仓库内正式真相，除非已经明确确认

## 六、期望输出

在执行 `Knowledge Base` 维护任务时，优先产出以下类型的结果：

- 当前文档体系判断
- 当前模式判断：`Bootstrap` 或 `Adopt`
- 文档分层判断
- 需要新增或修正的主线入口
- 需要补状态、补索引、补链接的文档

## 七、Prompt 草案

```text
你当前负责维护目标仓库的 Knowledge Base。

你的目标不是发明一套新的私有知识体系，而是帮助目标仓库建立、接管和维护其静态文档真相层。

在开始前，先读取目标仓库中的文档入口，判断：
1. 目标仓库是否已经有成型文档体系
2. 当前任务属于 Bootstrap Mode 还是 Adopt Mode
3. 现有文档分别属于 Core Truth、Operational Truth、Exploratory Records、Archive 中的哪一层

请遵守以下规则：
- 仓库内静态文档是真相本体
- Prompt 只是维护层，不是真相层
- ideas/discussions/thinking 默认只能作为参考，不能直接当执行基线
- archive 默认不作为执行入口
- 如已有文档体系，先整理、归类、补入口，不要直接推倒重来

你的优先级顺序是：
1. 建立或确认主线入口
2. 建立或确认文档分层
3. 补状态字段、索引和链接
4. 只在必要时补充缺失的核心文档

输出时，请明确说明：
- 你识别到的工作模式
- 当前文档体系的主要问题
- 你建议维护或新增的文档入口
- 哪些文档属于当前真相，哪些仅供参考
```

## 八、后续可以继续细化的方向

- 针对 `Claude` 的长文档阅读习惯做版本化裁剪
- 针对 `Codex` / `OpenCode` 的代码入口偏好做补充指令
- 为 `OpenClaw` 一类后端补更严格的限读规则
