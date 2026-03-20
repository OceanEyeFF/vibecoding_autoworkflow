---
title: "Knowledge Base Skill 骨架"
status: draft
updated: 2026-03-20
owner: aw-kernel
last_verified: 2026-03-20
---
# Knowledge Base Skill 骨架

> 目的：定义 `knowledge-base-skill` 的最小职责和输入输出，用于后续落成真实 Skill。

## 一、Skill 名称

`knowledge-base-skill`

## 二、职责

- 判断仓库文档体系处于 `Bootstrap Mode` 还是 `Adopt Mode`
- 识别文档分层
- 补主线入口、状态字段、索引和链接

## 三、触发场景

- 仓库缺少成型文档体系
- 仓库已有文档，但结构混乱或主线不清
- 需要接管现有文档体系，而不是推倒重来

## 四、输入

- 当前仓库已有文档入口
- 当前任务目标
- `Knowledge Base` 相关基线和 Prompt 规范

## 五、输出

- 当前模式判断：`Bootstrap` 或 `Adopt`
- 文档分层判断
- 建议新增或修正的主线入口
- 需要补状态、补索引、补链接的文档清单

## 六、主要读取入口

- [Knowledge Base 基线](/mnt/e/repos/wsl/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/knowledge-base.md)
- [Knowledge Base 适配 Prompt 草案](/mnt/e/repos/wsl/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/prompts/knowledge-base-adapter-prompt.md)
- [Memory Side 总览](/mnt/e/repos/wsl/personal/vibecoding_autoworkflow/docs/knowledge/memory-side-baseline.md)

## 七、硬性约束

- 不把 Prompt 当成项目真相
- 不默认重写整个文档体系
- 不把 `Exploratory Records` 直接提升为主线
- 不把 `Archive` 当执行入口

## 八、当前实际 Skill 落点

```text
toolchain/skills/aw-kernel/memory-side/knowledge-base-skill/
  SKILL.md
  agents/
    openai.yaml
  references/
    entrypoints.md
```

当前实际入口：

- [knowledge-base-skill/SKILL.md](/mnt/e/repos/wsl/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/knowledge-base-skill/SKILL.md)
- [knowledge-base-skill/references/entrypoints.md](/mnt/e/repos/wsl/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/knowledge-base-skill/references/entrypoints.md)

## 九、建议被谁调用

- `task-entry-agent`
- 后续可能的 `memory-side-agent`

## 十、判断标准

- Skill 能稳定输出文档体系判断
- Skill 能指出主线入口而不是扩散阅读范围
- Skill 产物能直接支撑后续 `context-routing-skill`
