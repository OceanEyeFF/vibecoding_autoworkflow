---
title: "Skill Deployment 维护流"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Skill Deployment 维护流

> 目的：为当前仓库的 repo-local / global skill mounts 提供统一的维护节奏，避免只会“重新部署”，却看不见 drift、陈旧 target 和坏链路。

先建立通用边界，再读本页：

- [根目录分层](../knowledge/foundations/root-directory-layering.md)
- [Toolchain 分层](../knowledge/foundations/toolchain-layering.md)

本页只负责仓库实现层的维护动作，不定义 skill 真相。

## 一、推荐维护循环

默认维护顺序固定为：

1. `verify`
2. `local` 或 `global` deploy
3. 再跑一次 `verify`

这能区分三种情况：

- 是 source 没有变化，但 target 漂移了
- 是 target 需要重新同步
- 是 deploy 后仍然存在结构问题

## 二、Repo-local 维护

检查 repo-local mounts：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

重新同步 repo-local mounts：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode
```

如果怀疑 target 里残留了旧目录，可以带 `--prune`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents --prune
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude --prune
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode --prune
```

部署后再复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

## 三、全局安装维护

检查全局 target 时，优先显式传目标根，避免受环境变量差异影响。

示例：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --target global \
  --backend agents \
  --agents-root ~/.codex/skills
```

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --target global \
  --backend claude \
  --claude-root ~/.claude/skills
```

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --target global \
  --backend opencode \
  --opencode-root ~/.config/opencode/skills
```

部署全局 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend agents \
  --agents-root ~/.codex/skills \
  --create-roots
```

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend claude \
  --claude-root ~/.claude/skills \
  --create-roots
```

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend opencode \
  --opencode-root ~/.config/opencode/skills \
  --create-roots
```

如需清理全局 target 中的陈旧目录：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend opencode \
  --opencode-root ~/.config/opencode/skills \
  --create-roots \
  --prune
```

## 四、`verify` 当前会检查什么

- target root 是否存在
- target root 类型是否正确
- 是否缺少预期 skill 目录
- 是否存在没有 source 对应关系的陈旧 target
- repo-local mount 是否是坏链路
- repo-local mount 的 symlink 目标是否正确
- global target 是否错误地变成 symlink 或普通文件

`verify` 发现 drift 时会返回非零退出码，适合直接挂进手工检查或 CI。

## 五、什么时候使用 `--prune`

适合在下面几种场景使用：

- 某个 backend 的 skill 名发生收口或删除
- target 目录里混入了历史实验目录
- 你明确希望 target 和 `product/.../adapters/<backend>/skills/` 一致

不适合在下面几种场景默认使用：

- 你还没先跑过一次 `verify`
- 你不确定 target 里是否有临时手工实验内容

## 六、非目标

本页不是：

- research runner 使用手册
- canonical skill 规则正文
- 自动同步 daemon 设计
- 多 agent 编排方案

本页只负责：

- deploy target 维护节奏
- `verify` / `deploy` / `--prune` 的最小使用方式
- repo-local 与 global mounts 的检查顺序
