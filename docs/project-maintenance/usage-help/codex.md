---
title: "Codex Usage Help"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# Codex Usage Help

> 目的：只保留 `agents` backend 的特有差异，回答 “Codex target root 怎么解析、root 参数怎么传、按新三步主流程时有什么 backend 特有注意事项、真实 Harness manual run 怎么进入”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [aw-installer Public Quickstart Prompts](../deploy/aw-installer-public-quickstart-prompts.md)
- [aw-installer External Trial Feedback Contract](../deploy/aw-installer-external-trial-feedback.md)
- [npx Command Test Execution](../testing/npx-command-test-execution.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与 target root

- backend 名：`agents`
- 默认 target root：`.agents/skills/`
- 显式覆盖参数：`--agents-root`

说明：

- 如果没有 `--agents-root`，当前命令默认落到 repo-local `.agents/skills/`
- 如果你要把 target root 指到别处，再显式传 repo-local 或 disposable 路径，例如 `--agents-root "$PWD/.agents/skills"`
- `--agents-root` 只能指向目标 repo 内受控 `.agents/skills` 目录或专用临时 skills 目录；不要指向 home 目录、`.ssh`、shell 配置目录、系统配置目录或其他敏感可写路径
- 外部试用优先从目标仓库根目录运行 pre-release `.tgz` 命令，并显式清空 `AW_HARNESS_REPO_ROOT` 与 `AW_HARNESS_TARGET_REPO_ROOT`；这样 source payload 来自 package，target repo root 来自当前工作目录
- 已有工作内容的目标仓库必须先看 `diagnose` 和 dry-run `update`，确认 planned paths 只落在目标仓库 `.agents/skills/aw-*` 受管目录后，再执行 `update --yes`
- deploy 主流程统一写在 [Deploy Runbook](../deploy/deploy-runbook.md)；本页只补 backend-specific 差异

## 二、Deploy verify 与真实 Harness 观察

`agents` 的最小 deploy 验证是 destructive reinstall 主流程加只读 `verify`。这只证明 payload source、target root 与 live install 对齐，不证明 Harness runtime 行为。

推荐顺序：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

如需观察真实 Harness 行为，使用 [Codex Post-Deploy Behavior Tests](../testing/codex-post-deploy-behavior-tests.md)。该 runbook 在临时 repo 中准备隔离 `.agents/skills/`，用无交互 `codex exec` 真实调用 `harness-skill`，观察空 repo 冷启动、`.aw/` 初始化、scope 切换与真实任务推进。

判断边界：

- `adapter_deploy.py verify --backend agents` 是 deploy target 对齐证明。
- `codex-post-deploy-behavior-tests.md` 是当前 operator-facing 的 Harness runtime 观察入口。
- skills mock / contract smoke 不再作为当前主线验证入口；后续 skill 行为调整由已准入测量资产或真实运行观察承接。

## 三、和其他 backend 的区别

- `agents` 默认使用 repo-local `.agents/skills/`
- 如需改 root，再显式传 `--agents-root`
- `agents` 继续使用和其他 backend 同一套 destructive reinstall 模型，不需要额外的 `agents` 专属 build 步骤
- backend 名仍是 `agents`；本轮不并入 `agents -> codex` 命名迁移

## 四、命令差异

`agents` backend 的主要差异只有 target root 参数：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents --agents-root "$PWD/.agents/skills"
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents --agents-root "$PWD/.agents/skills"
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents --agents-root "$PWD/.agents/skills"
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents --agents-root "$PWD/.agents/skills"
```

当前语义：

- 前三条构成主流程
- 最后一条是只读复验
- 如果你就在当前仓库下部署到默认 repo-local target，可以省略 `--agents-root`
- 不要把 `--agents-root` 指向与目标 repo 无关的敏感目录；外部试用优先使用默认 repo-local `.agents/skills/`
- 外部试用反馈优先使用 [trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 或 [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)。如果通过 [npx Command Test Execution](../testing/npx-command-test-execution.md) 复现，请附上脱敏后的 `aw-installer-npx-run.log` 摘要；不要在长期文档中记录私有仓库标识、token 或完整敏感日志
