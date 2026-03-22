---
title: "Writeback & Cleanup 适配 Prompt 草案"
status: draft
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Writeback & Cleanup 适配 Prompt 草案

> 目的：作为 `Claude`、`Codex`、`OpenCode`、`OpenClaw` 等后端可复用的通用 Prompt contract，指导 AI 在任务结束时为目标仓库生成统一的 `Writeback Card`。

## 一、适用场景

- 一轮编码或文档任务结束后，需要把结果回写到仓库文档
- 需要判断哪些内容已经足够稳定，可以进入主线
- 需要识别哪些旧入口、旧说明或旧 Prompt 应该被清理

## 二、核心原则

- 只有已验证结果才能进入回写决策
- 如果目标仓库已有 `Task Contract`，优先以它作为本轮目标和范围的来源
- 先判断写回层级，再执行文档修改
- Prompt 只指导收尾，不持有项目真相
- 探索过程默认不是主线回写对象
- 清理的目标是降噪，不是抹掉历史

## 三、工作目标

你的工作不是复述整个任务过程，而是为当前任务生成一张最小 `Writeback Card`，明确：

- 哪些变更已经被验证
- 这些变更应该写到哪一层
- 哪些内容当前不能写回
- 哪些旧资料需要清理、降级或更新

## 四、执行步骤

1. 先读取 `Task Contract` 或当前任务目标，再确认实际变更。
2. 读取相关验证结果。
3. 只提取已确认成立的变更事实。
4. 判断这些事实应写回 `Core Truth` 还是 `Operational Truth`。
5. 列出当前不应写回的内容。
6. 列出需要清理的旧入口、旧假设和旧 Prompt。
7. 用固定格式输出 `Writeback Card`。

## 五、硬性约束

- 没有验证依据前，不要声称某项变更已经可以进入主线
- 不要把任务过程摘要直接当成回写结果
- 不要把临时推理写入正式真相
- 不要因为“以后可能有用”就把大量过程信息写入主线文档
- 如果是否回写存在明显不确定性，应先标记待确认

## 六、期望输出

输出必须使用固定字段，至少包含：

- `task`
- `verified_changes`
- `non_changes`
- `write_to_core_truth`
- `write_to_operational_truth`
- `do_not_write_back`
- `cleanup_targets`
- `risks_left`
- `verification_basis`

格式约束见：

- [Writeback & Cleanup 输出格式](../formats/writeback-cleanup-output-format.md)

## 七、Prompt 草案

```text
你当前负责目标仓库的 Writeback & Cleanup。

你的职责不是重新执行任务，也不是写一份长篇复盘，而是在任务结束后为当前结果生成一张最小 Writeback Card。

请先确认以下内容：
1. 本轮任务原始目标是什么
2. 实际发生了哪些变更
3. 哪些变更已经有验证依据
4. 哪些项目文档可能因此需要同步更新

然后遵守以下规则：
- 只有已验证结果才能进入回写决策
- 如果目标仓库已有 Task Contract，优先以它作为本轮目标和范围来源
- Prompt 只负责指导收尾，不是真相层
- 探索过程默认不是主线回写对象
- 未验证猜测、临时推理、已否定方案默认不写回
- Cleanup 的目标是清理噪声，不是删除所有历史

你的输出目标是：
1. 明确哪些内容已被验证
2. 明确这些内容应写到 Core Truth 还是 Operational Truth
3. 明确哪些内容当前不要写回
4. 明确哪些旧入口、旧假设、旧 Prompt 需要清理或降级

请用固定格式输出 Writeback Card，至少包含：
- task
- verified_changes
- non_changes
- write_to_core_truth
- write_to_operational_truth
- do_not_write_back
- cleanup_targets
- risks_left
- verification_basis

如果当前验证证据不足，请明确标出待确认项，不要强行把内容写入主线文档。
```

## 八、后续可继续细化的方向

- 为 `Codex` / `OpenCode` 补更强的代码变更回写约束
- 为 `Claude` 补更强的长文档更新裁剪规则
- 为不同仓库补“哪些入口文档必须同步更新”的项目级检查项
