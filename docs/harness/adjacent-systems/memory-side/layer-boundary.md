---
title: "Memory Side 层级边界"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Memory Side 层级边界

> 目的：把 `Memory Side` 里的通用能力合同、业务源码、repo-local deploy target 和评测资产明确拆开，避免继续把“框架语义”“源码实现”“本地挂载结果”混成一层。

它是根目录分层在 `Memory Side` 主题下的局部投影。更上层的根目录边界见：

- [根目录分层](../../../project-maintenance/foundations/root-directory-layering.md)

## 一、为什么要拆

当前仓库里当前主要存在三类对象，以及一层 repo-local 挂载：

- 定义 `Memory Side` 通用边界的知识文档
- repo-local `.agents/`、`.claude/`、`.opencode/` 下的部署结果与评测资产

如果这几类对象继续混写，后续开发很容易出现下面几种问题：

- 把 deploy target 当成业务源码
- 把 repo-local wrapper 当成通用 skill 合同
- 把本仓库目录结构误当成其他仓库的默认前提
- 把本仓库评测基线误当成跨仓库通用验收标准

## 二、三层主体 + 一层挂载

### 1. 通用合同层

职责：

- 定义 `Memory Side` 的能力模型
- 约束输入、输出和边界
- 面向“目标仓库”描述规则，而不是默认绑定当前仓库

当前属于这一层的内容：

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/knowledge-base.md`
- `docs/harness/adjacent-systems/memory-side/context-routing.md`
- `docs/harness/adjacent-systems/memory-side/writeback-cleanup.md`
- `docs/harness/adjacent-systems/memory-side/*-rules.md`
- `docs/harness/adjacent-systems/memory-side/formats/`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

### 2. 业务源码层

职责：

- 把通用合同变成可部署的 skill 与 adapter 源码
- 作为实际实现的 source of truth

当前状态：

- 当前仓库已移除 `product/memory-side/` 对应的源码树
- 如果未来恢复 executable source，应继续落在 `product/`，而不是写回 repo-local deploy target

硬要求：

- 业务源码只改 `product/`
- `.agents/`、`.claude/` 与 `.opencode/` 不能替代这一层

### 3. 仓库实现层

职责：

- 说明当前仓库如何实例化这些合同
- 说明本仓库的部署与 repo-local 使用方式

当前属于这一层的内容：

- `docs/project-maintenance/usage-help/`
- `toolchain/scripts/deploy/adapter_deploy.py`

### 4. Repo-local deploy target

职责：

- 为当前仓库提供快速测试挂载点
- 承接从 `product/` 同步出来的本地部署结果

当前属于这一层的内容：

- `.agents/skills/`
- `.claude/skills/`
- `.opencode/skills/`

硬要求：

- 必须在 `.gitignore` 中忽略
- 不手工维护源码
- 不冒充通用合同层或业务源码层

## 三、推荐阅读顺序

### 1. 需要理解 `Memory Side` 能力模型时

先读：

- [Memory Side 总览](./overview.md)
- [Memory Side Skill 与 Agent 模型](./skill-agent-model.md)
- 对应 partition 基线和规则文档

不要先读：

- `.agents/skills/`
- `.claude/skills/`
- `.opencode/skills/`
- repo-local deployment guide

### 2. 需要改业务源码时

先读通用合同层，再进入源码层：

1. [Memory Side 总览](./overview.md)
2. [Memory Side Skill 与 Agent 模型](./skill-agent-model.md)
3. 确认当前仓库是否重新准入了 `product/` 下的对应源码层

### 3. 需要在本仓库部署或维护时

先读通用合同层，再读仓库实现层，最后再看 deploy target：

1. [Memory Side 总览](./overview.md)
2. [Memory Side Skill 与 Agent 模型](./skill-agent-model.md)
3. `docs/project-maintenance/usage-help/`
4. `toolchain/scripts/`
5. `.agents/skills/`、`.claude/skills/` 或 `.opencode/skills/`

## 四、措辞规范

通用合同层优先使用：

- “目标仓库”
- “目标项目”

仓库实现层可以使用：

- “本仓库”
- “当前仓库”
- “repo-local deploy target”

## 五、失败信号

如果出现下面任一现象，说明分层又开始混了：

- 通用合同层开始默认引用 `.agents/`、`.claude/` 或 `.opencode/`
- 业务源码被直接改回 `.agents/`、`.claude/` 或 `.opencode/`
- deploy target 被当成 source of truth
- repo-local guide 开始把自己描述成跨仓库通用默认方案
- 评测场景只覆盖本仓库，却被当成通用验收标准
