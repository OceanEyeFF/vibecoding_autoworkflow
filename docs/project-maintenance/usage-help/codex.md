---
title: "Codex Usage Help"
status: active
updated: 2026-04-19
owner: aw-kernel
last_verified: 2026-04-19
---
# Codex Usage Help

> 目的：只保留 `agents` backend 的特有差异，回答 “Codex target root 怎么解析、root 参数怎么传、按新三步主流程时有什么 backend 特有注意事项、最小 deploy / contract smoke 怎么做”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与 target root

- backend 名：`agents`
- 默认 target root：`.agents/skills/`
- 显式覆盖参数：`--agents-root`

说明：

- 如果没有 `--agents-root`，当前命令默认落到 repo-local `.agents/skills/`
- 如果你要把 target root 指到别处，再显式传 `--agents-root /your/custom/skills`
- deploy 主流程统一写在 [Deploy Runbook](../deploy/deploy-runbook.md)；本页只补 backend-specific 差异

## 二、最小 deploy / contract smoke 口径

`agents` 是当前有稳定 deploy / contract smoke 口径的 backend 之一。前提是先完成主流程，再跑一次只读 `verify`，然后执行仓库内的 repeatable contract smoke harness。

推荐顺序：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

建议做法：

- 直接运行：

```bash
python3 toolchain/scripts/test/agents_first_wave_contract_smoke.py
```

- 这条 contract smoke 会在隔离 install root 和生成的 `.aw` fixture 上完成：
  - `prune --all -> check_paths_exist -> install -> verify`
  - 已安装 first-wave skill copy 的真实读取
  - `harness -> repo-status -> repo-whats-next -> init-worktrack -> dispatch` 最小路径
  - `dispatch-skills` 的 fallback / general-executor 路径
- 它证明的是 deploy target、payload / output field contract、`.aw` scaffold，以及一条最小 bounded route 到 `dispatch` 选择。
- 它不证明真实 Harness runtime、真实 Codex 无交互连续执行、真实任务连续推进，或真实 delegated subagent dispatch。
- 如需保留现场，显式传 root：

```bash
python3 toolchain/scripts/test/agents_first_wave_contract_smoke.py \
  --agents-root .autoworkflow/state/agents-first-wave-smoke/.agents/skills \
  --aw-root .autoworkflow/state/agents-first-wave-smoke/.aw
```

判断标准：

- contract smoke 命令返回 `PASS`
- five-skill first-wave 路径全部经过
- `dispatch-skills` 证明 fallback/general-executor 路径，而不是只验证 mount 存在
- 这一步是 deploy / contract smoke，不替代 `adapter_deploy.py verify`

## 三、和其他 backend 的区别

- `agents` 默认使用 repo-local `.agents/skills/`
- 如需改 root，再显式传 `--agents-root`
- `agents` 继续使用和其他 backend 同一套 destructive reinstall 模型，不需要额外的 `agents` 专属 build 步骤
- backend 名仍是 `agents`；本轮不并入 `agents -> codex` 命名迁移

## 四、命令差异

`agents` backend 的主要差异只有 target root 参数：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents --agents-root /your/custom/skills
python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents --agents-root /your/custom/skills
python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents --agents-root /your/custom/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents --agents-root /your/custom/skills
```

当前语义：

- 前三条构成主流程
- 最后一条是只读复验
- 如果你就在当前仓库下部署到默认 repo-local target，可以省略 `--agents-root`
