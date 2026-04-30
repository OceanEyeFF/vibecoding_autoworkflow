---
title: "Claude Adapter Source"
status: active
updated: 2026-05-01
owner: aw-kernel
last_verified: 2026-05-01
---
# Claude Adapter Source

> 目的：固定 `claude` backend 的 payload source 边界，让 `install --backend claude`、`diagnose --backend claude --json`、`verify --backend claude` 和 `update --backend claude` 使用同一套 canonical-copy 读取面。

本页属于 [Deploy Runbooks](./README.md) 系列文档。先读 [Deploy Mapping Spec](./deploy-mapping-spec.md)。

## 一、范围

当前 `claude` backend 分发完整 Harness skill set，但仍是 `agents` mainline 旁路的 Claude Code 适配 lane，不替代 `agents` 主路径。

当前准入的 payload 与 `agents` backend 对齐，覆盖 `product/harness/skills/` 下的 19 个 canonical Harness skills。完整 Claude runtime 发现机制、user-home 全局安装策略和稳定/latest 发布语义不由本页定义。

## 二、目录落点

`claude` backend 的 payload source 固定落在：

- `product/harness/adapters/claude/skills/<skill>/`

当前 target root 默认为：

- `<target_repo>/.claude/skills/`

可通过当前命令的 `--claude-root` 显式覆盖 target root。该覆盖只影响 target，不改变 source root。

canonical truth 仍在：

- `product/harness/skills/<skill>/`

repo-local `.claude/skills/` 是 deploy target，不是 source truth。

## 三、Payload Contract

当前 payload 使用：

- `payload_version: claude-skill-payload.v1`
- `backend: claude`
- `payload_policy: canonical-copy`
- `reference_distribution: copy-listed-canonical-paths`
- `target_dir: <skill_id>`
- `target_entry_name: SKILL.md`
- `legacy_target_dirs: ["aw-<skill_id>"]` where an older managed Claude compatibility install may exist

Claude payload may also declare:

- `claude_frontmatter.disable-model-invocation: true`

When this field is present, install writes the target `SKILL.md` with the requested Claude frontmatter override while keeping canonical source under `product/harness/skills/` unchanged.

`required_payload_files` 必须等于 `canonical_paths` 相对 `canonical_dir` 的文件集合，再加上：

- `payload.json`
- `aw.marker`

`aw.marker` 由 deploy 写入 target 时生成，不存在于 adapter source 中。它只证明 target 目录是当前 backend 的受管 live install，不是 source truth 或历史记录。

## 四、命令边界

当前支持：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py diagnose --backend claude --json
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py update --backend claude
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend claude
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
```

`update --backend claude --yes` 仍只是 `prune --all -> check_paths_exist -> install -> verify` 的显式 one-shot 包装。它不做 channel 解析、自升级、验签或自动回滚。

## 五、验证要求

涉及 `claude` adapter payload source 的改动至少验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest toolchain/scripts/test/test_agents_adapter_contract.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'`
- `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude`
- `node --check toolchain/scripts/deploy/bin/aw-installer.js`

如果同时改根 package packlist，还要验证：

- `npm pack --dry-run --json`
