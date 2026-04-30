---
title: "Memory Side Skill 与 Agent 模型"
status: active
updated: 2026-04-30
owner: aw-kernel
last_verified: 2026-04-30
---
# Memory Side Skill 与 Agent 模型

> 目的：定义 `Memory Side` 中合同正文、`Skill` 与可选调用层的关系，并明确 `Task Contract` 这个任务接口对象如何与它们衔接。

## 一、为什么不能停在合同正文

只靠合同正文也能定义行为边界，但还不够成为稳定产物。

原因：

- 合同正文解决“是什么”，不解决“怎么触发”
- 合同正文解决“语义约束”，不解决“能力封装”
- 合同正文解决“跨后端共识”，不解决“多后端部署”

因此，`Memory Side` 的可落地形态不能只有 docs 层合同正文。

## 二、四类载体

### 1. 合同正文

职责：

- 定义跨后端共享的行为语义
- 约束每个能力的输入、输出和边界

### 2. Skill

职责：

- 把单一能力封装成可复用的执行单元
- 指定何时触发、读取哪些文档、输出什么结构

### 3. Task Contract

职责：

- 把讨论收束成正式执行基线
- 为 `Context Routing` 和后续执行层提供同一份目标、范围和验收边界

说明：

- 它是任务接口对象，不属于 `Memory Side` 三个组件本体
- 但它是当前仓库保留的关键上游对象

### 4. Agent / Workflow Shell

职责：

- 在宿主执行层决定何时调用哪个 Skill
- 串联任务开始前和任务结束后的上下文维护动作

说明：

- 这是可选调用层，不是当前仓库知识主线的一部分
- 当前仓库不固定 `task-entry-agent`、`task-closeout-agent` 一类命名
- 当前仓库也还没有稳定产品化的 `skill -> subagent dispatch shell`
- 因此，“选择了 skill” 不自动等于 “一定会 fork 一个独立 agent”
- 如果 host runtime 没有显式 dispatch 能力，skill round 仍可能由当前 carrier 承接；这属于 runtime fallback，不应被伪装成独立 subagent 已经落地

## 三、当前仓库里的四层落点

### 1. 知识合同层

包括：

- `docs/harness/adjacent-systems/memory-side/` 下的基线、规则、格式和模型说明

### 2. 可执行源码层

说明：

- 这层在概念上仍然存在
- 但当前仓库已不再保留 `product/memory-side/` 与 `product/task-interface/` 的对应源码树
- 如果未来重新引入 executable source，仍应回到 `product/`，而不是写进 deploy target 或 docs

### 3. 部署结果层

包括：

- `.agents/skills/`
- `.claude/skills/`

说明：

- 这里是 repo-local deploy target
- 它们从 `product/` 同步出来
- 它们不是 source of truth

### 4. 工具层

包括：

- `toolchain/scripts/`

说明：

- 工具层负责部署、治理检查和按需准入的辅助脚本入口
- 工具层不再保存 canonical skill 源码

边界说明见：

- [Memory Side 层级边界](./layer-boundary.md)

## 四、Memory Side 的固定 Skill 集

当前阶段只建议 3 个 Skill：

- `knowledge-base-skill`
- `context-routing-skill`
- `writeback-cleanup-skill`

说明：

- 这 3 个 skill 只覆盖 `Memory Side`
- `task-contract-skill` 属于 `Task Interface`，不计入 `Memory Side` skill 集

对应关系：

| Skill | 对应 Partition | 核心产物 |
|---|---|---|
| `knowledge-base-skill` | `Knowledge Base` | 文档体系判断、主线入口修正、分层归类 |
| `context-routing-skill` | `Context Routing` | `Route Card` |
| `writeback-cleanup-skill` | `Writeback & Cleanup` | `Writeback Card` |

## 五、当前保留的任务接口对象

当前阶段不在知识主线中定义任务级 Agent 集。

当前保留并建议优先固化的任务接口对象只有：

### `Task Contract`

职责：

- 把讨论压成正式执行基线
- 作为 `Context Routing` 的上游输入
- 作为执行层和收尾动作共享的边界说明

如果某个宿主执行层未来需要定义任务级 Agent，它们也应消费：

- `Task Contract`
- `Route Card`
- `Writeback Card`

当前仓库不再保留 `Task Interface` 的直接 product 调用载体；若未来恢复，也只应作为合同正文的下游实现。

## 六、当前仓库中的落点

### 1. 合同与模型正文

当前仓库保留：

- `docs/harness/adjacent-systems/memory-side/` 下的合同正文
- `docs/harness/adjacent-systems/task-interface/` 下的任务接口合同

### 2. Repo-local deploy target

```text
.agents/
  skills/

.claude/
  skills/
```

说明：

- 这些目录只保留部署结果
- 当前 `.agents/skills/` 与受控 `.claude/skills/` compatibility payload 通过 `toolchain/scripts/deploy/adapter_deploy.py` 从 `product/` destructive reinstall 到 repo-local target
- `.claude/skills/` 可以作为 repo-local deploy target 保留，当前仓库只提供受控 `claude` compatibility backend
- 不应再手工维护源码

### 3. Toolchain

```text
toolchain/
  scripts/
```

说明：

- `deploy/adapter_deploy.py` 当前负责 `agents` backend 的 repo-local destructive reinstall 与只读 `verify`
- `test/path_governance_check.py` 负责轻量路径治理回归

## 七、与不同后端的关系

无论是 `Codex` 还是 `Claude`，都应共享同一套：

- 合同正文与字段约束
- Skill 输入输出约束
- `Task Contract / Route Card / Writeback Card` 这组接口对象
- canonical skill 源码

后端差异只应体现在：

- adapter frontmatter 或 interface metadata
- 本地挂载路径
- 各 CLI 的安装与调用方式

## 八、当前阶段不做什么

- 不直接为每个后端分别写一整套独立知识文档
- 不把 deploy target 当成 source of truth
- 不把 Skill 做成隐藏规则黑箱
- 不在知识主线中固定任务级 Agent 命名
- 不先把 `Codex` / `Claude` 扩成复杂 subagents catalog

## 九、配套文档

- [Memory Side 层级边界](./layer-boundary.md)
- [Usage Help 总入口](../../../project-maintenance/usage-help/README.md)
- [Codex Repo-local Usage Help](../../../project-maintenance/usage-help/codex.md)
- [Claude Repo-local Usage Help](../../../project-maintenance/usage-help/claude.md)
