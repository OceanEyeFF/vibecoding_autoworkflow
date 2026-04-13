---
title: "Skill 生命周期维护"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Skill 生命周期维护

> 目的：把 `add / update / rename / remove` 收成统一入口，明确 source of truth、deploy target、verify 和文档同步的最小闭环。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Deploy Runbook](./deploy-runbook.md)

## 一、适用范围

本页适合在下面场景先读：

- 你新增了 canonical skill 或 backend wrapper
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

## 三、`Add`

### 改哪里

- 新增 canonical skill 时，改 `product/<partition>/skills/`
- 新增 backend wrapper 时，改 `product/<partition>/adapters/<backend>/skills/`

### 同步哪里

- 对使用中的 backend 执行 `local` 或 `global` deploy
- 如果新增 skill 改变了入口、合同或最近导航，同步对应 `docs/deployable-skills/` 或入口 `README`

### 跑什么 verify

- 先 deploy，再跑：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend <backend>
```

- `agents` 与 `claude` 如需确认运行侧可读，再去各自 usage-help 做 smoke verify

### 文档要不要同步

- 如果只是实现细节变化，通常不需要
- 如果新增了正式 skill、入口、调用边界或 operator 应知动作，需要同步 `docs/`

## 四、`Update`

### 改哪里

- 只改 `product/` 下的 canonical skill 或 adapter wrapper

### 同步哪里

- 对正在使用的 target 重新 deploy

### 跑什么 verify

推荐最小节奏：

1. `verify`
2. `local` 或 `global` deploy
3. 再 `verify`

### 文档要不要同步

- 若没有改变入口、合同或 operator 行为，通常不需要
- 若改变了固定输出、调用方式或运行要求，需要同步相应文档

## 五、`Rename`

### 改哪里

- 在 `product/` 里完成 source rename
- 同步更新引用该 skill 的入口、交叉链接和必要文档

### 同步哪里

- 对相关 backend 重新 deploy
- deploy 后检查 target 是否残留旧 skill 名

### 跑什么 verify

推荐最小节奏：

1. 先跑 `verify`，确认当前 drift
2. 执行 `local` 或 `global` deploy
3. 如 target 残留旧目录，再带 `--prune`
4. 再跑一次 `verify`

### 文档要不要同步

- 要。rename 通常意味着入口、链接、引用名都要跟着收口

## 六、`Remove`

### 改哪里

- 删除 `product/` 下对应 source

### 同步哪里

- 先看 target 是否还残留旧 skill
- 再对相关 backend 执行 deploy；必要时带 `--prune`

### 跑什么 verify

推荐最小节奏：

1. 先 `verify` 看是否出现 stale target
2. 执行 `local/global deploy --prune`
3. 再 `verify`

### 文档要不要同步

- 要。删除正式 skill 后，要同步清理入口页、引用和说明

## 七、新增 Partition / Adapter 来源时的同步要求

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

## 八、每类动作的最小 Verify

| 动作 | 最小验证 |
|---|---|
| `Add` | deploy 后跑 `verify --backend <backend>`；`agents / claude` 视需要补 smoke verify |
| `Update` | `verify -> deploy -> verify` |
| `Rename` | 先 `verify` 看 drift；deploy 后如有旧名残留再 `--prune`；最后复验 |
| `Remove` | 先 `verify` 看 stale target；deploy 时视情况 `--prune`；最后复验 |

如果同一 skill 同时被 repo-local 和 global target 使用，两边都要复验。

## 九、常见误区

- 直接改 `.agents/`、`.claude/`、`.opencode/`，把 deploy target 当 source of truth
- 新增或删除 skill 后只跑 deploy，不先看 `verify` 暴露出来的 drift
- rename 后只确认新名存在，没有检查旧 target 是否残留
- remove 后忘记 `--prune`，导致 target 看起来“还能用”但其实已经偏离 source
- 把 backend usage-help 当成通用 deploy 文档，结果重复解释 lifecycle
