---
title: "Context Routing 输出格式"
status: active
updated: 2026-03-19
owner: aw-kernel
last_verified: 2026-03-19
---
# Context Routing 输出格式

> 目的：为 `Context Routing` 规定固定输出格式，避免不同 AI 后端各自生成风格差异很大的阅读入口说明。

## 一、输出对象

`Context Routing` 的标准输出对象叫 `Route Card`。

它是当前任务的最小上下文入口卡片，不是知识库副本，也不是执行计划。

## 二、固定字段

### 必填字段

```text
task_type:
goal:
read_first:
read_next:
code_entry:
do_not_read_yet:
stop_reading_when:
```

### 选填字段

```text
scope_hint:
verification_entry:
optional_background:
open_questions:
```

## 三、字段含义

- `task_type`
  当前任务类型，只写一个主类型。

- `goal`
  当前任务要解决什么，尽量压成一到两句。

- `read_first`
  开始执行前必须先读的文档入口，数量尽量少。

- `read_next`
  在 `read_first` 之后再读的补充入口，用于补足约束、变更或局部背景。

- `code_entry`
  与任务直接相关的代码入口、目录或测试入口，不扩大到无关区域。

- `do_not_read_yet`
  当前阶段先不要读的资料范围，用来防止上下文污染。

- `stop_reading_when`
  说明什么时候应停止继续扩读并进入执行。

- `scope_hint`
  说明本轮只覆盖哪些边界，避免扩写。

- `verification_entry`
  如果当前任务一开始就需要关注验证入口，可以提前标出。

- `optional_background`
  仅当主线资料不足时才考虑读取的背景材料。

- `open_questions`
  当前生成 `Route Card` 时还缺什么最小信息。

## 四、格式约束

- 每个字段都尽量短
- 优先列入口，不写长解释
- `read_first` 和 `read_next` 都应是有限集合，不应无限扩张
- `do_not_read_yet` 必须明确写出禁读范围，不能留空
- 如果信息不足，优先写 `open_questions`，不要改成全仓扫描

## 五、推荐模板

下面模板使用的是当前推荐目录布局，只是示例，不代表所有目标仓库都必须逐字采用同一路径。

```text
task_type: Feature
goal: 为目标仓库补一条新的写回规则，并保持现有知识分层不变。
scope_hint: 只涉及目标仓库的 Memory Side 文档，不进入运行时实现设计。
read_first:
- docs/knowledge/memory-side/overview.md
- docs/knowledge/memory-side/knowledge-base.md
- docs/knowledge/memory-side/context-routing.md
read_next:
- docs/knowledge/memory-side/context-routing-rules.md
- docs/knowledge/foundations/partition-model.md
code_entry:
- docs/knowledge/
do_not_read_yet:
- docs/archive/
- 无关的 ideas / discussions / thinking
- Flow Side 运行时实现细节
stop_reading_when:
- 已确认当前任务所属 Partition
- 已确认相关文档入口和边界
- 已能直接开始编辑目标文档
verification_entry:
- 检查新增文档是否与现有基线定义冲突
optional_background:
- docs/reference/
open_questions:
- 当前任务是否需要同步补 Writeback 规则
```

## 六、判断标准

如果下面几句话成立，说明输出格式是合格的：

- 不同后端能产出结构接近的 `Route Card`
- 执行端看到卡片后可以直接开始阅读
- 卡片会压缩上下文，而不是扩大上下文
