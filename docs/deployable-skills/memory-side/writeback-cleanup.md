---
title: "Writeback & Cleanup 基线"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Writeback & Cleanup 基线

> 目的：定义 `Writeback & Cleanup` 在 `Memory Side` 中的职责，只回答“任务结束后怎么统一回写项目真相并清理噪声”。

## 一、组件

`Writeback & Cleanup`

## 二、功能

- 把已验证结果写回仓库内静态文档
- 更新变更摘要、风险、待办和入口链接
- 清理失效 Prompt、旧假设和过期入口

## 三、目标

- 让任务结果回到项目真相，而不是留在对话里
- 让下一轮 AI 读取的是刷新后的主线文档
- 减少旧 Prompt 和伪事实持续污染后续任务

## 四、当前最合适的实现形态

- 固定格式更新规则
- 清理检查清单
- `writeback-cleanup-skill`
- 文档维护 Prompt 或 repo-local 收尾模板

说明：

- 当前阶段重点是“怎么更新”和“更新到哪里”
- 不必先实现成专门的任务级 Agent 或交互模块

## 五、最小回写内容

- 改了什么
- 没改什么
- 验证了什么
- 还有什么风险
- 哪些文档需要同步更新

## 六、最小清理内容

- 已失效的 Prompt
- 已被证伪的旧假设
- 已过期的文档入口
- 会误导后续 AI 的阶段性说明

## 七、不做什么

- 不把未经验证的内容写回项目真相
- 不只提交代码而跳过文档维护
- 不把已过期的入口继续保留为主线入口

## 八、判断标准

如果下面三句话成立，说明 `Writeback & Cleanup` 是清楚的：

- 本轮任务结果能回到仓库文档
- 下一轮 AI 不需要重新猜上轮做了什么
- 旧噪声不会继续占据主线入口

## 九、配套文档

为了把 `Writeback & Cleanup` 落成可执行产物，当前配套文档包括：

- [Writeback & Cleanup 回写规则](./writeback-cleanup-rules.md)
- [Writeback & Cleanup 适配 Prompt 草案](./prompts/writeback-cleanup-adapter-prompt.md)
- [Writeback & Cleanup 输出格式](./formats/writeback-cleanup-output-format.md)
- [Writeback & Cleanup Skill 骨架](./skills/writeback-cleanup-skill.md)
