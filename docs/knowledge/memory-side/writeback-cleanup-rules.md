---
title: "Writeback & Cleanup 回写规则"
status: active
updated: 2026-03-20
owner: aw-kernel
last_verified: 2026-03-20
---
# Writeback & Cleanup 回写规则

> 目的：把 `Writeback & Cleanup` 从抽象职责落实成实际的任务收尾规则，回答“本轮结果哪些要写回、写到哪里、哪些不要写、哪些旧内容要清理”。

## 一、收尾对象

`Writeback & Cleanup` 的直接产物是一张 `Writeback Card`。

它只回答四类问题：

- 本轮哪些内容已经被验证
- 这些内容应该写回哪一层文档
- 哪些内容当前不能写回
- 哪些旧内容需要清理或降级

它不是任务复盘，也不是完整执行日志。

## 二、输入

生成 `Writeback Card` 时，只使用下面几类输入：

- 当前任务目标和范围
- 本轮已完成的代码或文档变更
- 已完成的验证结果
- 当前 `Knowledge Base` 中受影响的文档入口

## 三、统一收尾步骤

1. 先列出本轮已经确认发生的变更。
2. 再列出本轮明确没有变的边界。
3. 只把已验证内容映射到对应文档层级。
4. 标出不能写回的内容。
5. 检查是否存在需要清理的旧入口、旧假设和旧 Prompt。

## 四、回写分层规则

### 1. 写回 `Core Truth`

适用于：

- 已稳定的模块边界
- 新的接口或规则
- 已确认的主线结构变化
- 已确认的长期约束

限制：

- 没有验证依据，不进入 `Core Truth`
- 只影响当前一次任务说明的内容，不进入 `Core Truth`

### 2. 写回 `Operational Truth`

适用于：

- 当前任务状态
- 已完成内容摘要
- 已知风险
- 待办、后续动作、近期变更

限制：

- 不把长期规则误写成短期状态
- 不把探索过程误写成当前项目状态

### 3. 留在 `Exploratory Records`

适用于：

- 方案比较
- 未定稿分析
- 思考过程
- 候选方向

限制：

- 默认不提升为执行主线
- 只有在明确确认后，才允许上升到 `Core Truth` 或 `Operational Truth`

### 4. 不写回

下面内容默认不进入仓库主线：

- 未验证猜测
- 对话中的临时推理
- 已被否定的方案
- 只对本轮工具操作有意义的细碎过程信息

## 五、最小回写要求

每轮任务结束后，至少要回答下面问题：

- 改了什么
- 没改什么
- 基于什么验证
- 哪些真相文档需要同步更新
- 还剩哪些风险和后续动作

## 六、清理规则

`Cleanup` 的目标不是删历史，而是防止旧噪声继续占据主线入口。

默认需要检查：

- 已失效的 Prompt
- 已被证伪的旧假设
- 已过期的文档入口
- 与当前主线冲突的阶段性说明
- 应该降级为参考资料、但仍停留在主线位置的旧内容

## 七、最小清理检查清单

每轮收尾至少检查下面几项：

- 是否有入口文档还在指向旧结构
- 是否有状态字段需要更新
- 是否有旧风险已经失效但仍保留为当前风险
- 是否有探索文档误占主线入口
- 是否有阶段性 Prompt 被误当成长期规则

## 八、禁写与限写规则

- 不把未经验证的内容写回项目真相
- 不只更新代码而完全跳过文档回写
- 不把探索性判断直接覆盖主线入口
- 不把历史错误结论继续保留为当前说明
- 当信息不足以安全回写时，宁可标记待确认，也不要强行写入

## 九、Writeback Card 最小要求

每张 `Writeback Card` 至少包含：

- `task`
- `verified_changes`
- `non_changes`
- `write_to_core_truth`
- `write_to_operational_truth`
- `do_not_write_back`
- `cleanup_targets`
- `risks_left`
- `verification_basis`

固定格式见：

- [Writeback & Cleanup 输出格式](/mnt/e/repos/wsl/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/formats/writeback-cleanup-output-format.md)

## 十、判断标准

如果下面几句话成立，说明回写规则是有效的：

- 本轮已验证结果能落回正确层级
- 下一轮 AI 不需要重新猜本轮到底改了什么
- 旧噪声不会继续停留在主线入口
