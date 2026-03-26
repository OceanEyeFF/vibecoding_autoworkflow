---
title: "OpenCode Memory Side Repo-local Adapter 部署帮助"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# OpenCode Memory Side Repo-local Adapter 部署帮助

> 目的：说明如何把 `product/` 下的 OpenCode adapter 源码部署到本仓库 `.opencode/`，或安装到全局 OpenCode skills 根目录。本页属于仓库实现层，不是跨仓库通用合同。

先建立通用边界，再读本页：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Skill Deployment 维护流](../skill-deployment-maintenance.md)

本页当前只采用一层验证：

- `sync verify`：通过 `adapter_deploy.py verify` 检查 `.opencode/skills/` 的同步状态

当前不写成已支持：

- `smoke verify`

说明：

- 当前部署脚本按 backend 汇总部署 `product/` 下的所有 adapter skill。
- 如果仓库同时存在 `Task Interface` skill，它也会一起挂载到 `.opencode/skills/`。
- 本页只约束其中 `Memory Side` 这一组 skill 的边界和检查项。

## 一、当前落点

```text
docs/knowledge/
  memory-side/
    ...

product/memory-side/
  skills/
  adapters/
    opencode/
      skills/

.opencode/
  skills/

toolchain/scripts/
  deploy/
    adapter_deploy.py
```

职责边界：

- `docs/knowledge/` 是真相层
- `product/memory-side/skills/` 是 canonical skill 源码
- `product/memory-side/adapters/opencode/` 是 OpenCode adapter 源码
- `.opencode/skills/` 是 repo-local deploy target

## 二、部署原则

- 不把项目真相搬进 `.opencode/skills/`
- 不直接手工维护 `.opencode/skills/`
- 不把 `.opencode/skills/` 当成第二真相层
- 业务源码始终改在 `product/`

## 三、本地挂载

默认把 adapter 源码以软链方式挂到本仓库 `.opencode/skills/`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode
```

做 dry run：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode --dry-run
```

先做 repo-local 检查：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

如需清理陈旧 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode --prune
```

部署后复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

当前边界：

- `OpenCode` 当前只确认 deploy sync 成立
- 不把 `OpenCode` 写成已经具备稳定 smoke verify 口径
- 如需进一步 runtime 验证，应等独立 contract 明确后再补

## 四、全局安装

默认把 adapter 复制到 OpenCode 的全局 skills 根目录：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --dry-run
```

默认根目录解析规则：

- 优先使用 `--opencode-root`
- 否则使用 `$XDG_CONFIG_HOME/opencode/skills`
- 如果没有设置 `XDG_CONFIG_HOME`，则回落到 `~/.config/opencode/skills`

显式指定目标根：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend opencode \
  --opencode-root ~/.config/opencode/skills \
  --create-roots
```

如需检查全局目标：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --target global \
  --backend opencode \
  --opencode-root ~/.config/opencode/skills
```

全局维护同样只停在 `sync verify`：

- 先检查 target 是否与 source 同步
- 不在本页声明 OpenCode runtime smoke 已可作为稳定维护动作

## 五、最小检查项

- `product/memory-side/adapters/opencode/skills/*/SKILL.md` 先读 canonical skill，再读 canonical docs
- `.opencode/skills/` 由部署脚本生成，而不是手工维护
- skill 输出仍然使用 canonical docs 中定义的固定格式
- adapter 内没有复制 `Memory Side` 规则正文

## 六、相关文档

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
- [Knowledge Base canonical skill](../../../product/memory-side/skills/knowledge-base-skill/SKILL.md)
- [Context Routing canonical skill](../../../product/memory-side/skills/context-routing-skill/SKILL.md)
- [Writeback & Cleanup canonical skill](../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md)
