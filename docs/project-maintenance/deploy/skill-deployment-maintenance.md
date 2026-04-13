---
title: "Skill Deployment 维护流"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Skill Deployment 维护流

> 目的：为当前仓库的 repo-local / global skill mounts 提供统一的维护与诊断入口，回答“怎么复验、怎么处理 drift、什么时候该 `--prune`、故障信号分别表示什么”。

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

## 三、验证分层

### 1. `sync verify`

用途：

- 检查 deploy target 是否和 `product/.../adapters/<backend>/skills/` 同步
- 发现缺失 mount、坏链路、错误类型和陈旧 target
- 对 `harness-operations` 的 local mounts 额外检查 symlink 是否指向当前 build root，以及 build output 是否和 canonical `prompt.md + harness-standard.md + references/` 一致
- 对 global copied targets 额外检查 copy 内容是否和当前 canonical harness snapshot 一致

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

### 2. `smoke verify`

用途：

- 在 backend 自己的真实运行环境里做最小可用性确认
- 确认 backend 不只是“挂载结构存在”，而是真的能读取对应 wrapper

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
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root ~/.codex/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```

重新同步全局 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root ~/.codex/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
```

需要清理陈旧全局 target 时再带 `--prune`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root ~/.codex/skills --create-roots --prune
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots --prune
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots --prune
```

## 六、`--prune` 的边界

适合在这些场景使用：

- skill 被删除
- skill 名发生 rename
- target 里残留历史目录
- 你明确希望 target 和 source 完全一致

不适合默认使用的场景：

- 还没先跑过一次 `verify`
- 还没确认 target 里的额外目录是不是手工实验目录

## 七、常见故障信号

### 1. `missing-target-entry`

含义：

- source 已存在，但 target 里缺少预期 mount
- 常见于新增 skill、新增 partition 来源后还没重新 deploy

处理顺序：

1. 先跑 `verify` 确认缺的是哪个 entry
2. 执行对应 backend 的 `local` 或 `global` deploy
3. 再跑一次 `verify`

### 2. unexpected stale target

常见信号：

- `unexpected-target-entry`

含义：

- target 里有 source 不再承认的旧 skill 或历史目录

处理顺序：

1. 先确认它不是手工实验目录
2. 如果确认是历史残留，再执行 deploy 时带 `--prune`
3. 再跑一次 `verify`

### 3. broken symlink / wrong type

常见信号：

- `broken-symlink`
- `wrong-target-type`
- `wrong-symlink-target`
- `wrong-target-root-type`
- `missing-build-source`
- `stale-build-source-file`
- `missing-build-source-file`

含义：

- repo-local mount 结构损坏
- local target 本该是 symlink，却变成目录或文件
- global target 本该是目录 copy，却变成 symlink 或文件
- harness repo-local mount 指向的 build source 缺失、过期，或内容和当前 canonical snapshot 不一致

处理顺序：

1. 先确认 target root 本身可用
2. 如为 harness source 问题，先执行 `build --backend <backend>`
3. 执行对应 backend 的 deploy，重建正确结构
4. 再跑一次 `verify`

### 5. global copy 内容漂移

常见信号：

- `missing-target-file`
- `stale-target-file`
- `unexpected-target-file`

含义：

- global target 目录虽然还存在，但内容已经和当前 source snapshot 不一致
- 对 harness skills，这个 snapshot 会按当前 `header.yaml + harness-standard.md + prompt.md + references/` 重新计算

处理顺序：

1. 先确认当前 canonical source 是预期版本
2. 重新执行对应 backend 的 `global` deploy
3. 再跑一次 `verify`

### 4. rename / remove 后的 drift

常见信号：

- 新名字报 `missing-target-entry`
- 旧名字报 `unexpected-target-entry`

含义：

- source 已经变了，但 target 还残留旧名

处理顺序：

1. 先 `verify` 看新旧名字各自的状态
2. 重新 deploy
3. 如果旧名仍残留，再带 `--prune`
4. 再复验一次 `verify`

## 八、额外判断

如果看到：

- `missing-target-root`

先判断这是“还没安装”还是“已安装 target 丢失”。首次安装场景应回到 [deploy-runbook.md](./deploy-runbook.md)；已有安装意外缺失时，再按本页维护循环处理。
