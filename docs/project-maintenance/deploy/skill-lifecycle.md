---
title: "Skill 生命周期维护"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Skill 生命周期维护

> 目的：把 `add / update / rename / remove` 收成统一入口，明确 source of truth、deploy 跟进、verify 与 writeback 的最小闭环。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Deploy Runbook](./deploy-runbook.md)

## 一、适用范围

本页适合在下面场景先读：

- 你新增了 canonical skill 或 backend adapter source
- 你更新了已有 skill，准备同步到 target
- 你要重命名或删除 skill
- 你新增了新的 partition / adapter 来源，想知道 deploy 层要补什么同步

本页不负责：

- backend-specific smoke verify 细节
- drift 故障诊断展开
- canonical skill 合同正文
## 二、Source of Truth 与 Deploy Target 边界

固定边界：

- source of truth 在 `product/`
- deploy target 在 `.agents/`、`.claude/`、`.opencode/` 或对应 global roots
- `docs/deployable-skills/` 负责合同与入口，不替代源码
- `usage-help/` 只补 backend 特有差异，不重复通用 deploy 流程

因此：

- 改 skill 内容时先改 `product/`
- 只有 deploy 后，repo-local / global target 才会反映 source 变化
- 只有已经验证过的变化，才写回 `docs/`
## 三、Harness source 变更和其他 backend source 的区别

`memory-side` 与 `task-interface` 的 adapter source 直接位于：

- `product/<partition>/adapters/<backend>/skills/<skill>/`

`harness-operations` 不一样。它的 source 由三部分组成：

- canonical prompt：`product/harness-operations/skills/<skill>/prompt.md`
- shared standard：`product/harness-operations/skills/harness-standard.md`
- backend header：`product/harness-operations/adapters/<backend>/skills/<skill>/header.yaml`

因此当你修改 harness skill 时：

- 不要把 deploy target 当 source 去改
- 不要把 backend 差异重新写回 canonical `prompt.md`
- 需要通过 `build` 或后续 `local/global` deploy 刷新 assembled `SKILL.md`

## 四、动作矩阵

| 动作 | 先改哪里 | deploy 跟进 | 文档跟进 |
|---|---|---|---|
| `Add` | 新 skill 的 canonical source；必要时补 backend adapter source | 对实际使用的 target scope 执行 `local` / `global` deploy，再按同一 scope `verify` | 若新增正式入口、调用边界或 operator 行为，同步入口页 |
| `Update` | 现有 canonical source 或 adapter source | 按实际 target scope 做 `verify -> deploy -> verify` | 只有 operator-facing 语义改变时才同步 docs |
| `Rename` | `product/` 中 source rename，并同步引用名 | 按实际 target scope 做 `verify -> deploy -> 按需 --prune -> verify` | 要同步入口、链接和引用名 |
| `Remove` | 删除 `product/` 中对应 source | 先按实际 target scope `verify` 看 stale，再 `deploy --prune`，最后复验 | 要同步清理入口和说明 |

如果同一 skill 同时被 repo-local 和 global target 使用，两边都要复验。

## 五、各动作的最小闭环

### 1. `Add`

- 新增 canonical skill 时，改 `product/<partition>/skills/`
- 新增 backend adapter source 时，改 `product/<partition>/adapters/<backend>/skills/`
- 新增 harness skill 时，同时检查 `prompt.md`、`references/`、`header.yaml` 是否齐全
- 对使用中的 target scope 执行 deploy，再跑对应 scope 的 verify：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend <backend>
```

- 如果你维护的是 global target，把这一步改成 `verify --target global`，并显式传 `--agents-root`、`--claude-root` 或 `--opencode-root`
- `agents` 与 `claude` 如需确认运行侧可读，再去对应 `usage-help` 做 smoke verify

### 2. `Update`

- 只改 `product/` 下 source，不手工改 `.agents/`、`.claude/`、`.opencode/`
- harness source 变更后，如果你要先看组装结果，可先跑：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend <backend>
```

- 最小节奏仍然是：

1. `verify`
2. `local` 或 `global` deploy
3. 再 `verify`

这里的 `verify` 也按实际 target scope 选择；global target 不要漏掉对应 root 参数。

### 3. `Rename`

- 在 `product/` 完成 source rename
- 同步更新引用该 skill 的入口、交叉链接和必要文档
- 最小节奏：

1. `verify`
2. `local` 或 `global` deploy
3. 如 target 残留旧目录，再带 `--prune`
4. 再 `verify`

如果 rename 影响 repo-local 和 global 两边安装，两边都要各自跑完整闭环。

### 4. `Remove`

- 删除 `product/` 下对应 source
- 最小节奏：

1. `verify`
2. `local/global deploy --prune`
3. 再 `verify`

## 六、新增 Partition / Adapter 来源时的同步要求

当你新增 `product/<partition>/adapters/<backend>/skills/` 下的新来源时：

- 已存在的 repo-local / global target 不会自动补齐新条目
- `verify` 通常会出现 `missing-target-entry`
- 处理顺序是：先 `verify` 确认，再执行对应 backend 的 deploy，再复验 `verify`

如果这个新增来源改变了：

- deployable skill 正式入口
- backend 支持边界
- operator 该去哪里看文档

还需要同步更新：

- `docs/deployable-skills/` 对应入口
- `docs/project-maintenance/deploy/` 对应入口
- 必要时对应 backend 的 `usage-help`

## 七、常见误区

- 直接改 `.agents/`、`.claude/`、`.opencode/`，把 deploy target 当 source of truth
- 把 harness backend 差异写进 canonical prompt，而不是写进 `header.yaml`
- 新增或删除 skill 后只跑 deploy，不先看 `verify` 暴露出来的 drift
- rename 后只确认新名存在，没有检查旧 target 是否残留
- remove 后忘记 `--prune`，导致 target 看起来“还能用”但其实已经偏离 source
- 把 backend `usage-help` 当成通用 deploy 文档，结果重复解释 lifecycle
