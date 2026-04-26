---
title: "Claude Harness Test Runbook"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
---
# Claude Harness Test Runbook

> 目的：给 Claude Code operator 一条隔离的 Harness runtime smoke 路径，用于确认 Claude 能读取项目级 skill entry，并能在临时 repo 中触发最小 `.aw/` 冷启动。本文不是 `claude` deploy adapter 合同。

先读：

- [Claude Repo-local Usage Help](../usage-help/claude.md)
- [Deploy Runbook](./deploy-runbook.md)
- [Skill 生命周期维护](./skill-lifecycle.md)

## 一、边界

- 当前仓库不提供 `adapter_deploy.py --backend claude`。
- 本 runbook 只覆盖 `set-harness-goal-skill/scripts/deploy_aw.py` 的 Claude 冷启动 helper。
- 所有写入都必须发生在临时 repo 或明确指定的测试 worktree。
- `.claude/skills/` 是 ignored repo-local deploy target / runtime mount，不是 source of truth。
- 成功标准是 Claude runtime 能读取 skill entry，并生成最小 Harness control-plane artifacts；不代表完整多轮 Harness 行为已经验证。

## 二、准备临时 repo

从本仓库根目录执行：

```bash
TMP_REPO="$(mktemp -d)"
git -C "$TMP_REPO" init

PYTHONDONTWRITEBYTECODE=1 python3 product/harness/skills/set-harness-goal-skill/scripts/deploy_aw.py \
  generate \
  --deploy-path "$TMP_REPO" \
  --baseline-branch main \
  --install-claude-skill
```

确认项目级 Claude skill 已安装：

```bash
find "$TMP_REPO/.claude/skills/aw-set-harness-goal-skill" -maxdepth 2 -type f | sort
```

期望：

- 至少存在 `SKILL.md`
- 不出现 symlink 写入
- 不需要当前仓库的 `adapter_deploy.py --backend claude`

## 三、Skill Entry 可读性 Smoke

在临时 repo 中运行非交互读取 smoke：

```bash
cd "$TMP_REPO"

claude --bare -p '/aw-set-harness-goal-skill
只做 smoke verify：读取这个 skill entry，输出你识别到的技能名称、用途和当前不应执行的写入动作。不要修改文件。'
```

通过标准：

- Claude 没有报告 unknown skill / unknown slash command。
- 输出能识别 `set-harness-goal-skill` 的用途。
- 输出明确没有执行文件写入。

失败处理：

- 如果 skill 不可识别，先检查 `$TMP_REPO/.claude/skills/aw-set-harness-goal-skill/SKILL.md` 是否存在。
- 如果 Claude 未读取项目级 skills，检查当前 Claude Code 版本、启动目录和项目 trust 状态。
- 不要改用 `adapter_deploy.py --backend claude` 兜底。

## 四、冷启动写入 Smoke

只在临时 repo 中执行：

```bash
cd "$TMP_REPO"

claude --bare --permission-mode acceptEdits -p '/aw-set-harness-goal-skill
在这个临时 repo 中初始化 Harness control plane。
目标：创建最小 `.aw/goal-charter.md`、`.aw/control-state.md` 和 `.aw/repo/snapshot-status.md`。
项目目标：验证 Claude Code 能通过项目级 skill entry 执行 Harness 冷启动。
非目标：不要创建业务源码，不要提交 git commit，不要调用 adapter_deploy.py。'
```

复验：

```bash
test -f .aw/goal-charter.md
test -f .aw/control-state.md
test -f .aw/repo/snapshot-status.md
git status --short --untracked-files=all
```

通过标准：

- 三个 `.aw/` control-plane 文件存在。
- `git status` 只显示临时 repo 中预期的 untracked runtime artifacts。
- 没有在当前源仓库写入 `.claude/`、`.aw/` 或业务源码。

## 五、记录证据

记录以下字段即可，不需要把完整 Claude 输出长期写入 docs：

- Claude Code 版本：`claude --version`
- 临时 repo 路径
- skill entry 路径
- smoke 命令退出码
- 冷启动后三个 `.aw/` 文件是否存在
- 是否出现 unknown skill / 权限拒绝 / 非预期写入

## 六、停止条件

遇到以下情况停止并回到文档或实现修复：

- Claude 无法识别项目级 skill entry
- 冷启动写入越过临时 repo
- 输出声称使用了当前仓库不存在的 `claude` deploy adapter
- `.aw/` artifact 缺失或明显不符合 Harness control-plane 结构
