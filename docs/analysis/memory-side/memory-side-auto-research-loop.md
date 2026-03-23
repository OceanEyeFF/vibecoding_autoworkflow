---
title: "Memory Side Repo-local Auto Research Loop"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# Memory Side Repo-local Auto Research Loop

> 目的：把 `karpathy/autoresearch` 的“固定程序 + 固定测量 + 反复试验”思路，改写成适用于本仓库 `Memory Side` Prompt / Skill adapter 优化的最小闭环。本页属于仓库实现层，不是跨仓库通用工作流合同。

先建立通用边界，再读本页：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)

## 一、当前优化对象

当前阶段不把 `Auto Research` 用在真相层上，而只用在适配层和评测程序上。

可优化层：

- `docs/knowledge/memory-side/prompts/`
- `product/memory-side/adapters/`
- `toolchain/evals/memory-side/program.md`

执行面：

- `.agents/skills/`
- `.claude/skills/`

不可在实验中漂移的层：

- `docs/knowledge/` 仍然是项目真相层
- `product/memory-side/skills/` 仍然是 canonical skill 源码层
- 基准场景 ID 和 JSON schema 仍然是稳定测量面

## 二、最小实验回路

建议先用下面的固定回路：

1. 选择一个稳定场景，例如 `CR-1` 或 `CR-2`
2. 固定 `program.md`、场景定义和输出 schema
3. 更新 `product/` 下的 adapter 源码
4. 用 `adapter_deploy.py local` 同步到 `.agents/` 或 `.claude/`
5. 分别用 `codex` 与 `claude` 的无交互模式跑一轮
6. 用同一套 rubric 判断是否更好

## 三、本仓库的最小 runner 落点

```text
toolchain/evals/memory-side/
  program.md
  scenarios.json
  scoring/
    context-routing-rubric.json
  schemas/
    knowledge-base-card.schema.json
    route-card.schema.json
    writeback-card.schema.json

toolchain/scripts/
  deploy/
    adapter_deploy.py
  research/
    memory_side_autoresearch.py
    memory_side_autoresearch_score.py
```

运行产物默认写到：

- `.autoworkflow/memory-side-autoresearch/`

## 四、最小使用方式

列出场景：

```bash
python3 toolchain/scripts/research/memory_side_autoresearch.py list
```

先把 adapter 同步到本地挂载点：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend all
```

做一次命令级 dry run：

```bash
python3 toolchain/scripts/research/memory_side_autoresearch.py run \
  --backend codex \
  --backend claude \
  --scenario CR-1 \
  --dry-run
```

## 五、当前阶段不做什么

- 不让 benchmark 直接修改 `docs/knowledge/`
- 不把 prompt 优化直接扩成复杂 agent swarm
- 不在没有固定 schema 的情况下比较输出好坏
- 不为了提分去放宽 truth boundary

如果后续要继续把这条方法扩到更多主题或更多 backend，先按：

- [Repo-local Eval 研究推进步骤](../eval-method-evolution.md)

## 六、相关文档

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Repo-local Adapter 评测基线](./memory-side-eval-baseline.md)
- [Repo-local Eval 研究推进步骤](../eval-method-evolution.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](../../operations/memory-side/codex-deployment-help.md)
- [Claude Memory Side Repo-local Adapter 适配帮助](../../operations/memory-side/claude-adaptation-help.md)
