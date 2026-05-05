---
title: "Memory Side Skill 与 Agent 模型"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Memory Side Skill 与 Agent 模型

> 目的：固定 `Memory Side` 合同正文、Skill、`Task Contract` 与可选调用层的关系。层级边界见 [layer-boundary.md](./layer-boundary.md)。

## 一、四类载体

| 载体 | 职责 | 不承接 |
| --- | --- | --- |
| 合同正文 | 定义跨后端共享的行为语义、输入输出和边界 | runtime 调用细节 |
| Skill | 封装单一能力，规定触发条件、读取入口和输出结构 | 项目长期真相 |
| Task Contract | 把讨论收束成正式执行基线，供 routing 和执行层消费 | Memory Side 三组件本体 |
| Agent / Workflow Shell | 宿主执行层决定如何调用 skill | 当前仓库知识主线 |

选择 skill 不自动等于 fork 独立 agent。宿主没有稳定 dispatch 能力时，skill round 可以由当前 carrier 承接，但必须标为 runtime fallback，不能伪装成独立 SubAgent 已落地。

## 二、Memory Side 固定 Skill 集

当前 Memory Side 只建议三类 skill：

| Skill | 对应组件 | 核心产物 |
| --- | --- | --- |
| `knowledge-base-skill` | `Knowledge Base` | 文档体系判断、主线入口修正、分层归类 |
| `context-routing-skill` | `Context Routing` | `Route Card` |
| `writeback-cleanup-skill` | `Writeback & Cleanup` | `Writeback Card` |

`task-contract-skill` 属于 `Task Interface`，不计入 Memory Side skill 集。

## 三、当前仓库落点

| 层 | 当前落点 | 说明 |
| --- | --- | --- |
| 合同与模型正文 | `docs/harness/adjacent-systems/memory-side/`、`docs/harness/adjacent-systems/task-interface/` | 上游真相 |
| 可执行源码层 | 当前不保留 `product/memory-side/` 或 `product/task-interface/` | 未来恢复时仍应落在 `product/` |
| Repo-local deploy target | `.agents/skills/`、`.claude/skills/` | 只承接安装结果，不是 source of truth |
| 工具层 | `toolchain/scripts/` | 部署、治理检查和辅助脚本 |

## 四、后端关系

`Codex` 与 `Claude` 应共享：

- 合同正文
- 字段约束
- Skill 输入输出约束
- `Task Contract / Route Card / Writeback Card`
- canonical skill source

后端差异只允许出现在：

- adapter metadata
- 本地挂载路径
- CLI 安装与调用方式

## 五、不做什么

- 不为每个后端复制一套独立知识文档。
- 不把 deploy target 当成 source of truth。
- 不把 Skill 做成隐藏规则黑箱。
- 不在知识主线中固定任务级 Agent 命名。
- 不把 `Codex` / `Claude` 扩成复杂 subagents catalog。

## 六、相关文档

- [Memory Side 层级边界](./layer-boundary.md)
- [Task Contract 基线](../task-interface/task-contract.md)
- [Usage Help 总入口](../../../project-maintenance/usage-help/README.md)
- [Codex Repo-local Usage Help](../../../project-maintenance/usage-help/codex.md)
- [Claude Repo-local Usage Help](../../../project-maintenance/usage-help/claude.md)
