---
title: "Knowledge Base Skill 骨架"
status: draft
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Knowledge Base Skill 骨架

> 目的：定义 `knowledge-base-skill` 的最小职责和输入输出，作为面向目标仓库的通用 skill contract。

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

- [Memory Side 层级边界](../layer-boundary.md)
- [Knowledge Base 基线](../knowledge-base.md)
- [Knowledge Base 适配 Prompt 草案](../prompts/knowledge-base-adapter-prompt.md)
- [Memory Side 总览](../overview.md)

## 七、硬性约束

- 不把 Prompt 当成项目真相
- 不默认重写整个文档体系
- 不把 `Exploratory Records` 直接提升为主线
- 不把 `Archive` 当执行入口

## 八、本文身份与本仓库中的落点

- 本文定义 `knowledge-base-skill` 的通用合同，不负责描述某个 repo-local wrapper。
- 当前仓库里的 canonical skill 实现在下面位置。

```text
product/memory-side/skills/knowledge-base-skill/
  SKILL.md
  references/
    entrypoints.md
```

当前实际入口：

- [knowledge-base-skill/SKILL.md](../../../../product/memory-side/skills/knowledge-base-skill/SKILL.md)
- [knowledge-base-skill/references/entrypoints.md](../../../../product/memory-side/skills/knowledge-base-skill/references/entrypoints.md)

## 九、建议接入方式

- 由人工文档治理任务直接触发
- 由 repo-local 任务入口模板、检查清单或 skill runner 触发
- 如果宿主执行层需要统一 caller，可自行命名，但不在本文固定 agent 名

## 十、判断标准

- Skill 能稳定输出文档体系判断
- Skill 能指出主线入口而不是扩散阅读范围
- Skill 产物能直接支撑后续 `context-routing-skill`
