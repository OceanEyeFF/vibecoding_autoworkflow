---
title: "Agents Adapter Source"
status: active
updated: 2026-04-20
owner: aw-kernel
last_verified: 2026-04-20
---
# Agents Adapter Source

> 目的：固定 `agents` backend payload source（后端负载源，即实际交付给后端使用的文件集合）结构，让 `install --backend agents` 与 `verify --backend agents` 都按同一读取面消费 canonical-copy payload descriptor，并把完整 canonical skill 内容复制到 target，而不是把 target 做成 repo-read-through 脚手架。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [First-Wave Skill Freeze](./first-wave-skill-freeze.md)

## 一、范围

本页只回答：

- `agents` backend 的 payload source 放在哪里
- 每个 payload 目录最小包含什么文件
- canonical skill copy（规范 skill 内容复制）必须遵守哪些 backend-specific（后端特定的）约束
- runtime `aw.marker` 在 destructive reinstall model 下承担什么角色

本页不定义：

- deploy target 的实现细节
- `adapter_deploy.py` 的内部状态机
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
- `schedule-worktrack-skill`
- `dispatch-skills`

canonical truth（权威源）仍在：

- `product/harness/skills/<skill>/`

## 三、每个 payload 目录的最小文件

每个 `agents` payload 目录当前最小只包含一个 source 文件：

### `payload.json`

这是 machine-readable payload descriptor（机器可读的负载描述文件）。

当前最小字段固定为：

- `payload_version`
- `payload_policy`
- `backend`
- `skill_id`
- `canonical_dir`
- `canonical_paths`
- `target_dir`
- `target_entry_name`
- `supported_target_scopes`
- `reference_distribution`
- `required_payload_files`
- `first_wave_profile`
- `first_wave_scope_kind`

只有当当前首发 contract 需要投影 canonical repo action 子集时，才允许将该字段写进 `payload.json` 中：

- `supported_repo_actions`

### runtime `aw.marker`

这是 deploy 写入 target 时动态生成的 machine-readable runtime artifact，不是 adapter source 文件。

当前字段固定为：

- `marker_version`
- `backend`
- `skill_id`
- `payload_version`
- `payload_fingerprint`

当前作用：

- 表达“这个 target 目录是否对应当前 source 生成的 deploy payload”
- 配合 deployed `payload.json`，让 `verify / prune / install` 判断当前目录是否属于当前 backend 的受管 live install
- 避免把目录归属、仓库身份或历史接管语义编码进 target marker

当前边界：

- source 目录中不存放 `aw.marker`
- `required_payload_files` 仍需要声明 `aw.marker`，因为 target 的运行时 payload 集仍包含它
- 真正写入 target 的 marker 必须与当前 `backend / skill_id / payload_version / payload_fingerprint` 一致
- `prune --all` 只会删除带可识别、且属于当前 backend 的 marker 目录
- 没有可识别 marker、marker 不可解析、marker 字段不匹配、或 fingerprint 不匹配的同名目录，都不属于可自动接管对象

## 四、当前 payload policy

`agents` first-wave payload 当前统一采用：

- `payload_policy: canonical-copy`
- `supported_target_scopes: ["local"]`
- `reference_distribution: copy-listed-canonical-paths`

含义如下：

- deploy source 只保留 payload descriptor；它不再保存 backend wrapper `SKILL.md`
- install 按 `payload.canonical_paths` 与 `payload.required_payload_files`，把 `product/harness/skills/` 中声明过的 canonical 文件复制到 target
- 当前 target 至少包含 canonical `SKILL.md`、已声明的 `references/` 或 `templates/`、顶层 `payload.json` 与 runtime-generated `aw.marker`
- `supported_target_scopes` 仍保留在 payload descriptor 中，但它不再对应 operator-facing 的 `local/global` 命令面；当前主流程只通过 `install --backend agents` 写入 resolved target root
- `target_dir` 相对 backend skills root；当前 `agents` 首发实例使用 `aw-<skill_id>`，并保留 `<skill_id>` 作为 `legacy_target_dirs` 用于升级清理，不得使用绝对路径或带 `.` / `..` 的跳出式路径段
- 对当前 `agents` first-wave payload，`target_dir` 的业务语义固定为 backend skills root 下的直接子目录名，不承接 nested / multi-segment target layout
- 当前 live bindings 内，`target_dir` 必须唯一；install 不会尝试用覆盖顺序解决冲突
- `canonical_paths` 必须保持在各自 skill 的 `canonical_dir` 内，不能通过 `.` / `..` 路径段跳出 skill 包
- `required_payload_files` 当前必须等于 `canonical_paths` 在 `canonical_dir` 下的相对路径集合，再加上 `payload.json + aw.marker`；其中 `aw.marker` 是 sync 写入 target 的 runtime-generated marker，而不是 adapter source 文件
- operator-facing deploy 主流程不再区分 `local/global` mode；install 只负责把当前 source 声明的 live payload 写入 resolved backend target root
- 这套 payload source 不承接 archive/history、旧版本保活或增量修复语义

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
- `schedule-worktrack-skill`
  - `full-skill`
- `dispatch-skills`
  - 只承接 bounded dispatch contract 与 fallback / general-executor 路径

如果 canonical source 允许更宽的动作空间，仍继续保留在 canonical 层；这里只收窄 `agents` first-wave 可分发面。

## 六、验收与验证

B3 完成后至少应满足：

- `product/harness/adapters/agents/skills/<skill>/` 已对六个 first-wave skills 建立 payload source
- 每个 payload 目录都能从 `payload.json` 直接追溯到 canonical source 与 target contract
- `install --backend agents` 产出的 target skill 目录都包含完整 canonical skill copy，而不是 wrapper 快捷方式
- 每个 `payload.json` 都能支持 destructive reinstall model 下的 install / verify 读取面

建议验证：

- `python3 -m pytest toolchain/scripts/test/test_agents_adapter_contract.py`
- `python3 -m pytest toolchain/scripts/deploy/test_adapter_deploy.py`
- `python3 -m pytest toolchain/scripts/test/test_governance_semantic_check.py`
