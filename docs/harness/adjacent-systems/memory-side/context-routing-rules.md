---
title: "Context Routing 规则"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Context Routing 规则

> 目的：规定任务开始前如何生成最小 `Route Card`。职责定义见 [context-routing.md](./context-routing.md)，输出格式见 [formats/context-routing-output-format.md](./formats/context-routing-output-format.md)。

## 一、输入

生成 `Route Card` 只使用：

- 用户当前任务
- 当前 repo 入口与治理规则
- 可用知识入口
- 与任务直接相关的代码、测试或脚本入口
- 已知禁读、限读或停止扩读规则

不基于猜测补全文档，不把 routing 写成执行计划。

## 二、统一步骤

1. 判断任务类型。
2. 选择最小 `read_first`。
3. 必要时补 `read_next`。
4. 标出 `code_entrypoints`。
5. 标出 `do_not_read_yet`。
6. 标出 `stop_reading_when`。
7. 如一开始就需要验证，列 `validation_entrypoints`。

## 三、任务类型

| 类型 | 默认 read_first | 默认 code_entrypoints |
| --- | --- | --- |
| `feature` | `docs/README.md`、相关模块 README、约束/设计入口 | 目标模块、相邻测试 |
| `bugfix` | 失败测试/日志入口、相关模块 README、治理约束 | 报错路径、相邻恢复路径、回归测试 |
| `refactor` | 分层边界、模块 owner、相关设计约束 | 被改模块、调用方、测试 |
| `docs` | 最近入口页、承接层正文、相关治理规则 | 通常为空；涉及脚本时列最小脚本入口 |
| `investigation` | 总入口、相关模块入口、已知 evidence | 只列调查所需入口，不扩成全仓扫描 |

## 四、默认阅读顺序

1. 根入口或当前模块入口。
2. 与任务直接相关的承接层正文。
3. 最近的治理/边界规则。
4. 最小代码或测试入口。
5. 停止扩读并开始执行或回报缺口。

如果已经拿到足够入口，不继续扩读历史记录、归档、deploy target 或 repo-local state。

## 五、禁读与限读

默认先不读：

- `.agents/`
- `.claude/`
- `.autoworkflow/`
- `.spec-workflow/`
- `.nav/`
- 无关 archive / historical evidence
- 无关 deploy target

只有任务明确需要 runtime target、兼容导航或历史 evidence 时才进入这些区域，并在 `Route Card` 里说明原因。

## 六、停止条件

停止 routing 的条件：

- 已确认任务承接层。
- 已拿到执行所需最小文档入口。
- 已拿到最小代码或测试入口。
- 继续扩读只会重复背景。
- 关键事实缺失，需要用户或上游 artifact 补充。

## 七、Route Card 最小要求

`Route Card` 至少包含：

- `task_type`
- `read_first`
- `read_next`
- `code_entrypoints`
- `do_not_read_yet`
- `stop_reading_when`
- `validation_entrypoints`
- `routing_notes`

## 八、判断标准

规则清楚时，应满足：

- 同类任务得到相近入口。
- 入口足够执行，但不复制知识库。
- 禁读范围明确。
- 停止扩读条件明确。
- 输出能直接被执行层消费。

## 九、相关文档

- [Context Routing](./context-routing.md)
- [Context Routing 输出格式](./formats/context-routing-output-format.md)
- [Memory Side 总览](./overview.md)
