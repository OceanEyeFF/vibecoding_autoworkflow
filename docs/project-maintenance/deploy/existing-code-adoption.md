---
title: "Existing Code Project Adoption"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Existing Code Project Adoption

> 目的：定义把已有代码库接入 Harness 初始化流程时，operator-facing 的 `.aw/repo/discovery-input.md` 生成边界。

本页属于 [Deploy Runbooks](./README.md)，只承接 adoption 生成边界。artifact 正文见 [Repo Discovery Input](../../harness/artifact/repo/discovery-input.md)；skill workflow 与可执行资产见 [`set-harness-goal-skill`](../../../product/harness/skills/set-harness-goal-skill/SKILL.md)。

## 适用场景

Existing Code Project Adoption 用于目标 repo 已经存在代码、文档、脚本或治理规则，但尚未建立 Harness `.aw/` 控制面，或尚未把既有事实接入 `set-harness-goal-skill` 初始化流程的场景。

权威边界：

| 层 | 路径 | 角色 |
| --- | --- | --- |
| canonical artifact definition | `docs/harness/artifact/repo/discovery-input.md` | 定义 discovery input 的语义与最低结构 |
| skill-owned template source | `product/harness/skills/set-harness-goal-skill/assets/repo/discovery-input.md` | 可执行模板来源 |
| runtime target | `.aw/repo/discovery-input.md` | 目标 repo 中的只读事实输入 |

## Operator 命令

当前脚本集成落在 `product/harness/skills/set-harness-goal-skill/scripts/deploy_aw.js`：

```bash
node product/harness/skills/set-harness-goal-skill/scripts/deploy_aw.js generate \
  --deploy-path "$TARGET_REPO" \
  --baseline-branch "$BASELINE_BRANCH" \
  --adoption-mode existing-code-adoption
```

默认/profile 生成会自动包含 `repo-discovery-input`；显式 `--template` 选择仍以调用方选择为准。

## 不变量

- `.aw/repo/discovery-input.md` 是只读事实输入，不是 goal truth。
- discovery 可以提供候选目标信号；确认后的长期目标只能写入 `.aw/goal-charter.md`。
- `repo/snapshot-status.md` 是初始化后的慢变量观测面，可以引用 discovery，但不应复制 discovery 原文。
- `control-state.md` 可以链接 discovery 作为证据或 note，但不得把 discovery 字段提升为控制指令。
- baseline branch 必须来自显式 `--baseline-branch` / `AW_BASELINE_BRANCH`，或来自可验证 ref；不能退回到 `init.defaultBranch` 或写死 `main`。
- 生成流程不得覆盖已有 `.aw/goal-charter.md`。
- adoption 模式不是 deploy target install 行为。
- adapter payload source 不能成为 artifact truth。

## 验证入口

本模式的脚本行为由以下测试覆盖：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_set_harness_goal_deploy_aw_node.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_set_harness_goal_deploy_aw.py`

如果改变 discovery artifact、skill asset、baseline branch 解析或 goal overwrite policy，必须同步更新 artifact 文档、skill 入口和对应测试。
