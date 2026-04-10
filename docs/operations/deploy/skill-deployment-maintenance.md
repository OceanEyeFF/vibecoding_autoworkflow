---
title: "Skill Deployment 维护流"
status: active
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---
# Skill Deployment 维护流

> 目的：为当前仓库的 repo-local / global skill mounts 提供统一的维护节奏，避免只会“重新部署”，却看不见 drift、陈旧 target 和坏链路。

本页属于 [Deploy / Verify / Maintenance](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)

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

当 `product/*/adapters/<backend>/skills/` 新增 partition 来源（例如新增 `harness-operations`）时，已存在的 repo-local mount 不会自动补齐新条目。此时 `verify` 会出现 `missing-target-entry`，`closeout_acceptance_gate.py` 的 `test_gate` 也会按真实 drift 失败（不属于 `missing-target-root` 可跳过场景）。处理方式是先执行对应 backend 的 `local` deploy，再复验一次 `verify`。

## 二、验证分层

当前把 deployment verification 分成两层：

### 1. `sync verify`

用途：

- 检查 deploy target 是否和 `product/.../adapters/<backend>/skills/` 同步
- 发现缺失 mount、陈旧 target、坏链路和错误路径类型
- 作为 repo-local / global deploy 的统一结构检查

当前支持：

- `agents`
- `claude`
- `opencode`

执行入口：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend <backend>
```

### 2. `smoke verify`

用途：

- 在 backend 自己的真实运行环境里，做最小可用性确认
- 确认 backend 不只是“挂载结构存在”，而是真的能读取对应 repo-local skill wrapper
- 只做最小项目级 skill 调用验证，不扩成 research runner 或长期评测

当前支持：

- `agents`
- `claude`

当前不支持：

- `opencode`

说明：

- `OpenCode` 当前只确认 deployment adaptation 成立
- 当前不把 `OpenCode` 写成 smoke verify 已稳定可做的 backend
- 如果后续有稳定 runtime contract，再单独补 smoke verify 口径

## 三、Repo-local 维护

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

## 四、全局安装维护

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

## 五、`verify` 当前会检查什么

- target root 是否存在
- target root 类型是否正确
- 是否缺少预期 skill 目录
- 是否存在没有 source 对应关系的陈旧 target
- repo-local mount 是否是坏链路
- repo-local mount 的 symlink 目标是否正确
- global target 是否错误地变成 symlink 或普通文件

`verify` 发现 drift 时会返回非零退出码，适合直接挂进手工检查或 CI。

## 六、Smoke Verify 的当前边界

`smoke verify` 当前只覆盖 `agents` 与 `claude`。

最小口径：

- `agents`：在 Codex / OpenAI 侧显式调用 repo-local `.agents/skills/` 下的 wrapper，确认固定格式输出成立
- `claude`：在 Claude 侧显式调用 repo-local `.claude/skills/` 下的 wrapper，确认固定格式输出成立
- `opencode`：当前不写成 smoke verify 已支持；只保留 `sync verify`

因此当前推荐节奏是：

1. 所有 backend 先做 `sync verify`
2. `agents` 与 `claude` 再按各自 runbook 做 `smoke verify`
3. `opencode` 当前停在 deploy sync 层，不补 runtime smoke 结论

## 七、什么时候使用 `--prune`

适合在下面几种场景使用：

- 某个 backend 的 skill 名发生收口或删除
- target 目录里混入了历史实验目录
- 你明确希望 target 和 `product/.../adapters/<backend>/skills/` 一致

不适合在下面几种场景默认使用：

- 你还没先跑过一次 `verify`
- 你不确定 target 里是否有临时手工实验内容

## 八、非目标

本页不是：

- research runner 使用手册
- canonical skill 规则正文
- 自动同步 daemon 设计
- 多 agent 编排方案

本页只负责：

- deploy target 维护节奏
- `verify` / `deploy` / `--prune` 的最小使用方式
- repo-local 与 global mounts 的检查顺序
