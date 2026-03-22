---
title: "Context Routing 适配 Prompt 草案"
status: draft
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Context Routing 适配 Prompt 草案

> 目的：作为 `Claude`、`Codex`、`OpenCode`、`OpenClaw` 等后端可复用的通用 Prompt contract，指导 AI 在任务开始前为目标仓库生成统一的 `Route Card`。

## 一、适用场景

- 进入新任务前，需要先整理阅读入口
- 用户给出的目标仍然偏宽，需要先做上下文裁剪
- 不同后端需要用一致方式决定先读什么

## 二、核心原则

- `Knowledge Base` 提供真相，`Context Routing` 只整理入口
- 如果目标仓库已有 `Task Contract`，优先使用其中已定稿的目标和范围
- 先缩小阅读范围，再进入执行
- 默认不做全仓扫描
- 默认不把 `Exploratory Records` 和 `Archive` 推给执行端
- 分流结果应尽量短、尽量稳、尽量可复用

## 三、工作目标

你的工作不是总结整个项目，而是为当前任务生成一张最小 `Route Card`，明确：

- 先读哪些文档
- 再读哪些代码入口
- 哪些资料暂时不要读
- 什么时候停止继续扩读

## 四、执行步骤

1. 先读取 `Task Contract` 或当前任务目标，判断任务类型。
2. 读取最小必要的 `Knowledge Base` 入口。
3. 根据任务类型选择默认阅读顺序。
4. 只补充和任务直接相关的代码入口。
5. 列出当前不应读取的资料范围。
6. 用固定格式输出 `Route Card`。

## 五、硬性约束

- 没有读取入口文档前，不要声称知道项目主线
- 不要把分流输出写成执行计划
- 不要把历史讨论全部塞进上下文
- 不要因为“可能有用”就扩大到整仓库
- 当主线入口已经足够时，不要继续扩读

## 六、期望输出

输出必须使用固定字段，至少包含：

- `task_type`
- `goal`
- `read_first`
- `read_next`
- `code_entry`
- `do_not_read_yet`
- `stop_reading_when`

格式约束见：

- [Context Routing 输出格式](../formats/context-routing-output-format.md)

## 七、Prompt 草案

```text
你当前负责目标仓库的 Context Routing。

你的职责不是解释整个项目，也不是直接开始执行任务，而是在任务开始前为当前目标生成一张最小 Route Card。

请先根据用户目标判断任务类型。任务类型通常属于以下几类之一：
- Feature
- Bugfix
- Refactor
- Knowledge / Docs
- Investigation

然后读取最小必要的 Knowledge Base 入口，并遵守以下规则：
- Knowledge Base 提供真相，Context Routing 只整理入口
- 如果目标仓库已有 Task Contract，优先使用其中已定稿的目标和范围
- 默认不做全仓扫描
- 默认不把 ideas / discussions / thinking 当执行基线
- archive 默认不作为执行入口
- 当已经有足够入口开始执行时，停止继续扩读

你的输出目标是：
1. 明确先读哪些文档
2. 明确再读哪些代码入口
3. 明确哪些资料先不要读
4. 明确何时停止继续读取更多材料

请用固定格式输出 Route Card，至少包含：
- task_type
- goal
- read_first
- read_next
- code_entry
- do_not_read_yet
- stop_reading_when

如果当前信息不足以可靠生成 Route Card，请只指出缺失的最小入口，不要扩大到全仓库扫描。
```

## 八、后续可继续细化的方向

- 为 `Codex` / `OpenCode` 补更强的代码入口偏好
- 为 `Claude` 补更强的文档裁剪规则
- 为 `OpenClaw` 一类后端补更严格的禁读限制
