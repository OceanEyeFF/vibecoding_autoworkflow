---
title: "OpenCode Task Interface Repo-local Adapter 部署帮助"
status: active
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---
# OpenCode Task Interface Repo-local Adapter 部署帮助

> 目的：说明如何把 `product/` 下的 `Task Interface` OpenCode adapter 源码部署到本仓库 `.opencode/`，或安装到全局 OpenCode skills 根目录。本页属于仓库实现层，不是跨仓库通用合同。

本页属于 [Task Interface Usage Help](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)

本页当前只采用一层验证：

- `sync verify`：通过 `adapter_deploy.py verify` 检查 `.opencode/skills/` 的同步状态

当前不写成已支持：

- `smoke verify`

说明：

- 当前部署脚本按 backend 汇总部署 `product/` 下的所有 adapter skill。
- 执行 `--backend opencode` 时，`Memory Side` 与 `Task Interface` 两组 skill 会一起挂载到 `.opencode/skills/`。
- 本页只约束其中 `Task Interface` 这一组 skill 的边界和检查项。

## 一、当前落点

```text
docs/knowledge/
  foundations/
    task-contract.md
  task-interface/
    task-contract.md
    skills/
      task-contract-skill.md

product/task-interface/
  skills/
    task-contract-skill/
  adapters/
    opencode/
      skills/
        task-contract-skill/

.opencode/
  skills/

toolchain/scripts/
  deploy/
    adapter_deploy.py
```

职责边界：

- `docs/knowledge/` 是真相层
- `product/task-interface/skills/` 是 canonical skill 源码
- `product/task-interface/adapters/opencode/` 是 OpenCode adapter 源码
- `.opencode/skills/` 是 repo-local deploy target

## 二、部署原则

- 不把 `Task Contract` 真相搬进 `.opencode/skills/`
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
- 不把 `OpenCode` 写成已经具备稳定 `task-contract-skill` smoke verify 口径
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

- `product/task-interface/adapters/opencode/skills/task-contract-skill/SKILL.md` 先读 canonical skill，再读 canonical docs
- `.opencode/skills/` 由部署脚本生成，而不是手工维护
- skill 输出仍然使用 `Task Contract` 的固定结构
- adapter 内没有复制 `Task Contract` 规则正文

## 六、相关文档

- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Task Contract Skill 骨架](../../knowledge/task-interface/skills/task-contract-skill.md)
- [Task Contract canonical skill](../../../product/task-interface/skills/task-contract-skill/SKILL.md)
