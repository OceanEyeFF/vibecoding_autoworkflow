---
title: "Skill Deployment 维护流"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Skill Deployment 维护流

> 目的：为当前仓库的 repo-local / global skill mounts 提供统一的维护与诊断入口，回答“怎么复验、怎么处理 drift、什么时候该 `--prune`、local/global verify 到底各看什么、故障信号分别表示什么”。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)

本页只负责维护与诊断；首次安装看 [deploy-runbook.md](./deploy-runbook.md)，生命周期动作看 [skill-lifecycle.md](./skill-lifecycle.md)。

## 一、什么时候看这页

适合在下面场景先读：

- 你已经有 target，想做日常同步与复验
- 你怀疑 mounts 和 source 漂移了
- 你需要判断是否该用 `--prune`
- 你在处理 stale target、坏链路或 rename / remove 后残留
- 你看到 `missing-build-source`、`wrong-target-type`、`unexpected-target-entry` 之类的错误码

## 二、推荐维护循环

默认顺序固定为：

1. 如需刷新或检查 harness 组装产物，先跑 `build`
2. `verify`
3. `local` 或 `global` deploy
4. 再跑一次 `verify`

这个顺序的目的：

- 先把需要的 harness 组装产物准备好，同时保持 `verify` 本身只读
- 再看清 drift 是什么
- 再决定只是重同步，还是要顺手清理 stale target
- 最后确认 deploy 后问题是否真的消失

如果本仓库还没有 harness runtime，而你接下来要跑 harness-driven workflow，先执行：

```bash
python3 toolchain/scripts/deploy/init_harness_project.py
```

## 三、`verify` 在看什么

### 1. 通用 `sync verify`

用途：

- 检查 deploy target 是否和 `product/.../adapters/<backend>/skills/` 同步
- 发现缺失 mount、坏链路、错误类型和陈旧 target
- 对 `harness-operations` 的 local mounts 额外检查 symlink 是否指向当前 build root，以及 build output 是否和 canonical snapshot 一致
- 对 global copied targets 额外检查 copy 内容是否和当前 canonical snapshot 一致

执行入口：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend <backend>
```

如果命中 `missing-build-source`，说明当前 backend 的 harness assembled source 不存在；先执行：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend <backend>
```

global target 复验时，优先显式传该 backend 对应的 root 参数：

- `agents`：`--agents-root`
- `claude`：`--claude-root`
- `opencode`：`--opencode-root`

### 2. local 与 global 的差异

`verify` 在两个 target scope 下关注的 drift 不同：

- `local`
  检查 `.agents/skills/`、`.claude/skills/`、`.opencode/skills/` 里的 entry 是否是正确 symlink。
- `global`
  检查全局 target 是否是目录 copy，以及 copy 出来的文件内容是否和当前 source snapshot 一致。

对 harness skills，差异更明显：

- `local verify`
  关注 repo-local symlink 是否指向 `.autoworkflow/build/adapter-sources/<backend>/<skill>/`，并检查 build root 里的 `SKILL.md + references/` 是否与 `header.yaml + harness-standard.md + prompt.md + references/` 的当前快照一致。
- `global verify`
  不关心 symlink，而是直接检查全局目录 copy 的文件内容是否与当前 harness assembled snapshot 一致。

这里的 operator-facing 目标形态是固定的：

- `local` 预期是 symlink
- `global` 预期是目录 copy

如果手工改过 target，或使用了和默认形态相反的 `--method`，`verify` 会把它报成 `wrong-target-type`。

因此：

- 你想确认 harness build 产物有没有过期，看 `local verify`
- 你想确认全局安装是不是拷贝了旧内容，看 `global verify`

### 3. `smoke verify`

用途：

- 在 backend 自己的真实运行环境里做最小可用性确认
- 确认 backend 不只是“挂载结构存在”，而是真的能读取对应 skill entry

当前边界：

- `agents`：支持
- `claude`：支持
- `opencode`：当前不写成稳定 smoke verify backend，只保留 `sync verify`

backend-specific smoke verify 口径看：

- [Codex Repo-local Usage Help](../usage-help/codex.md)
- [Claude Repo-local Usage Help](../usage-help/claude.md)
- [OpenCode Repo-local Usage Help](../usage-help/opencode.md)

## 四、Repo-local 维护

检查 repo-local mounts：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

需要显式检查组装产物时，可先跑：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend opencode
```

重新同步 repo-local mounts：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode
```

需要清理陈旧 target 时再带 `--prune`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents --prune
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude --prune
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode --prune
```

## 五、全局安装维护

检查全局 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```

如果你不想显式传 `--agents-root`，先在 shell 里 `export CODEX_HOME=/your/codex/home`；脚本只会在未传 `--agents-root` 时读取 `CODEX_HOME`，不会替你把空变量补成合法路径。

重新同步全局 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
```

需要清理陈旧全局 target 时再带 `--prune`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots --prune
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots --prune
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots --prune
```

## 六、故障信号怎么路由

| 信号 | 常见含义 | 优先处理方式 |
|---|---|---|
| `missing-target-root` | target 还没安装，或已安装 root 被删了 | 首次安装回 [deploy-runbook.md](./deploy-runbook.md)；非首次场景按本页维护循环重建 |
| `missing-target-entry` | source 已存在，但 target 少了预期 mount | `verify -> deploy -> verify` |
| `unexpected-target-entry` | target 残留 source 已不承认的旧目录 | 先确认不是手工实验目录，再按需 `deploy --prune` |
| `wrong-target-root-type` | target root 存在，但不是目录 | 修正 root 后重跑 deploy |
| `wrong-target-type` | local 本应是 symlink，或 global 本应是目录 copy | 重跑对应 deploy；必要时先清理坏 target |
| `broken-symlink` / `wrong-symlink-target` | repo-local mount 指向错了，或指向对象已不存在 | 重跑 local deploy；如是 harness，再检查 build root |
| `missing-build-source` | harness assembled source 不存在；`verify` 不会自动 build | 先 `build --backend <backend>`，再复验或重新 deploy |
| `missing-build-source-file` / `stale-build-source-file` / `unexpected-build-source-file` | harness build root 的组装内容已经和当前 canonical snapshot 不一致 | 先 `build` 刷新组装产物，再看是否还需 deploy |
| `missing-target-file` / `stale-target-file` / `unexpected-target-file` | global copy 内容已经和当前 source snapshot 不一致 | 重新执行对应 backend 的 global deploy，再复验 |

## 七、`--prune` 的边界

适合在这些场景使用：

- skill 被删除
- skill 名发生 rename
- target 里残留历史目录
- 你明确希望 target 和 source 完全一致

不适合默认使用的场景：

- 还没先跑过一次 `verify`
- 还没确认 target 里的额外目录是不是手工实验目录

## 八、额外判断

如果看到：

- `missing-target-root`

先判断这是“还没安装”还是“已安装 target 丢失”。首次安装场景应回到 [deploy-runbook.md](./deploy-runbook.md)；已有安装意外缺失时，再按本页维护循环处理。
