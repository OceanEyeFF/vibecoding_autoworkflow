---
title: "Writeback & Cleanup Skill 骨架"
status: draft
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Writeback & Cleanup Skill 骨架

> 目的：定义 `writeback-cleanup-skill` 的最小职责和输入输出，作为面向目标仓库的通用 skill contract。

## 一、Skill 名称

`writeback-cleanup-skill`

## 二、职责

- 根据已验证结果生成最小 `Writeback Card`
- 指定哪些内容写回 `Core Truth`、哪些写回 `Operational Truth`
- 指出哪些旧入口、旧说明和旧 Prompt 需要清理或降级

## 三、触发场景

- 一轮任务结束后
- 已经拿到本轮验证结果和变更结果
- 需要判断哪些文档应被同步更新

## 四、输入

- 当前任务目标和范围
- 本轮实际变更
- 本轮验证结果
- 当前受影响的文档入口

## 五、输出

- 一张固定格式的 `Writeback Card`

最小字段包括：

- `task`
- `verified_changes`
- `non_changes`
- `write_to_core_truth`
- `write_to_operational_truth`
- `do_not_write_back`
- `cleanup_targets`
- `risks_left`
- `verification_basis`

## 六、主要读取入口

- [Memory Side 层级边界](../layer-boundary.md)
- [Writeback & Cleanup 基线](../writeback-cleanup.md)
- [Writeback & Cleanup 回写规则](../writeback-cleanup-rules.md)
- [Writeback & Cleanup 输出格式](../formats/writeback-cleanup-output-format.md)
- [Writeback & Cleanup 适配 Prompt 草案](../prompts/writeback-cleanup-adapter-prompt.md)

## 七、硬性约束

- 没有验证依据，不进入主线回写
- 不把任务过程摘要直接当成回写结果
- 不把临时推理写入正式真相
- 不把 `Cleanup` 理解成删除全部历史

## 八、本文身份与本仓库中的落点

- 本文定义 `writeback-cleanup-skill` 的通用合同，不负责描述某个 repo-local wrapper。
- 当前仓库里的 canonical skill 实现在下面位置。

```text
product/memory-side/skills/writeback-cleanup-skill/
  SKILL.md
  references/
    entrypoints.md
```

当前实际入口：

- [writeback-cleanup-skill/SKILL.md](../../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md)
- [writeback-cleanup-skill/references/entrypoints.md](../../../../product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md)

## 九、建议被谁调用

- `task-closeout-agent`
- 后续可能的 `memory-side-agent`

## 十、判断标准

- Skill 能稳定输出结构一致的 `Writeback Card`
- Skill 能区分可写回事实和不可写回噪声
- Skill 产物能直接支撑文档回写与清理动作
