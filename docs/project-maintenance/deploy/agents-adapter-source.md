---
title: "Agents Adapter Source"
status: active
updated: 2026-04-16
owner: aw-kernel
last_verified: 2026-04-16
---
# Agents Adapter Source

> 目的：固定 B3 的 `agents` backend payload source（后端负载源，即实际交付给后端使用的文件集合）结构，让后续 B4 可以按同一读取面消费 thin-shell wrapper（薄壳包装文件，只包含引用和约束、不复制正文的轻量封装），同时避免将 canonical skill truth（技能权威定义，即 `product/harness/skills/` 下的原始 skill 内容）或 deploy target（部署目标）硬编码到 adapter 层。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [First-Wave Skill Freeze](./first-wave-skill-freeze.md)
- [Skill Manifest Schema](./skill-manifest-schema.md)

## 一、范围

本页只回答：

- `agents` backend 的 B3 payload source 放在哪里
- 每个 payload 目录最小包含什么文件
- thin-shell wrapper（薄壳包装文件）必须遵守哪些 backend-specific（后端特定的）约束

本页不定义：

- deploy target 的同步实现
- `adapter_deploy.py` 的内容复制、链接或 drift（差异/漂移）处理逻辑
- `claude` / `opencode` backend 的 payload source
- 非 first-wave skill 的 adapter 扩展

## 二、目录落点

`agents` backend 的 payload source 固定落在：

- `product/harness/adapters/agents/skills/<skill>/`

当前只建立 first-wave skill 子集：

- `harness-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `init-worktrack-skill`
- `dispatch-skills`

canonical truth（权威源）仍在：

- `product/harness/skills/<skill>/`

machine-readable manifest 仍在：

- `product/harness/manifests/agents/skills/<skill>.json`

## 三、每个 payload 目录的最小文件

每个 `agents` payload 目录最小只包含两类文件：

### 1. `SKILL.md`

这是 deploy target（部署目标）未来要暴露的 target entry（目标入口文件）原型文件。

它必须是 thin-shell wrapper，且至少包含：

- `## Canonical Source`
- `## Backend Notes`
- `## Deploy Target`

它必须做的事：

- 指向 canonical skill package 在仓库中的实际读取路径
- 指向对应 manifest 与 payload descriptor
- 明确记录 backend-specific 的 first-wave 约束
- 声明 target entry 名称、payload policy 和 references 分发策略

它不能做的事：

- 复制 canonical workflow 正文
- 复制 canonical output contract
- 重新定义 skill ontology（技能本体/概念体系）

### 2. `payload.json`

这是 B3 的 machine-readable payload descriptor（机器可读的负载描述文件）。

当前最小字段固定为：

- `payload_version`
- `backend`
- `skill_id`
- `manifest_path`
- `canonical_dir`
- `canonical_paths`
- `target_dir`
- `target_entry_name`
- `payload_policy`
- `supported_target_scopes`
- `reference_distribution`
- `required_payload_files`
- `first_wave_profile`
- `first_wave_scope_kind`

只有当上游 manifest 已声明 `supported_repo_actions` 时，才允许将该字段投影到 `payload.json` 中：

- `supported_repo_actions`

## 四、当前 payload policy

`agents` first-wave payload 当前统一采用：

- `payload_policy: thin-shell`
- `supported_target_scopes: ["local"]`
- `reference_distribution: repo-read-through-local-only`

含义如下：

- deploy source 只提供 thin-shell wrapper，不复制 canonical skill 正文
- wrapper 当前通过相对于仓库根目录的 canonical path，回读 `product/harness/skills/` 中的权威内容
- 这种回读形式当前只对 repo-local `.agents/skills/` 有效；因为 global target 位于 `$CODEX_HOME/skills`，不共享仓库根目录
- B3 不把 `references/`（引用资料）、`templates/`（模板）或其他 canonical（权威的）附件复制进 adapter source（适配器源目录）
- 因此，当前 B3 payload form 只定义 repo-local 可分发面；global payload form 仍待后续 contract 明确
- B4 若要消费当前 payload form，必须拒绝将其直接同步到 global target，直到 global-safe payload form 被正式定义
- `target_dir` 相对 backend skills root；当前 `agents` 首发实例使用 `<skill_id>`，而不是 `skills/<skill_id>`

## 五、首发 skill 的 backend-specific 收窄

当前 `agents` payload 只固定下列 first-wave 收窄：

- `harness-skill`
  - `full-skill`
- `repo-status-skill`
  - `full-skill`
- `repo-whats-next-skill`
  - 只承接 `enter-worktrack` 与 `hold-and-observe` 两个动作
- `init-worktrack-skill`
  - 只承接 branch、baseline、contract、initial queue 与 first handoff 五个概念域
- `dispatch-skills`
  - 只承接 bounded dispatch contract 与 fallback / general-executor 路径

如果 canonical source 允许更宽的动作空间，仍继续保留在 canonical 层；这里只收窄 `agents` first-wave 可分发面。

## 六、验收与验证

B3 完成后至少应满足：

- `product/harness/adapters/agents/skills/<skill>/` 已对五个 first-wave skills 建立 payload source
- 每个 payload 目录都能从 `payload.json` 追溯到 manifest 和 canonical source
- 每个 wrapper 都保持 thin-shell，不复制 canonical workflow / output contract
- 每个 `payload.json` 都明确声明当前只支持 repo-local target scope

建议验证：

- `python3 -m pytest toolchain/scripts/test/test_skill_manifest_contract.py`
- `python3 -m pytest toolchain/scripts/test/test_agents_adapter_contract.py`
- `python3 -m pytest toolchain/scripts/test/test_governance_semantic_check.py`
