---
title: "根目录分层"
status: active
updated: 2026-04-10
owner: aw-kernel
last_verified: 2026-04-10
---
# 根目录分层

> 目的：固定根目录分层与例外白名单，避免业务源码、文档真相、工具脚本、运行状态再次混层。

## 一、正式内容区

根目录只认三块正式内容区：

1. `product/`：业务代码唯一源码根
2. `docs/`：仓库文档与知识真相层
3. `toolchain/`：脚本、评测、测试、打包与部署工具

## 二、根目录层级模型

| 层级 | 根目录对象 | 职责 | 不应承载 |
|---|---|---|---|
| Entry Layer | `README.md` `INDEX.md` `GUIDE.md` `ROADMAP.md` `AGENTS.md` | 导航与入口 | 长期规则正文、repo-local 细节 |
| Product Layer | `product/` | 业务源码 | 真相正文、运行状态 |
| Truth Layer | `docs/` | 知识与治理文档 | deploy 结果、mount/state |
| Toolchain Layer | `toolchain/` | 脚本与评测工具 | 业务源码真相 |
| Repo-local Mount Layer | `.claude/` `.agents/` `.opencode/` | 本地挂载与 deploy target | 主线真相、业务源码 |
| Repo-local State Layer | `.autoworkflow/` `.spec-workflow/` `.serena/` | 运行状态与项目级配置记忆 | 主线入口、业务源码 |
| Repo-local Execution Config Layer | `.codex/` | repo-local 执行配置 | 长期真相正文、运行产物 |
| Compatibility Navigation Layer | `.nav/` | 兼容导航 | 结构定义与规则正文 |
| Compatibility Shim Layer | `tools/` | 兼容入口 shim | canonical 逻辑实现 |
| Local Ephemeral Cache Layer | `.pytest_cache/` | 本地测试缓存 | tracked 主线内容 |
| Repo Infra Layer | `.github/` `.git/` `.gitignore` `.gitattributes` `.claudeignore` `LICENSE` `CONTRIBUTING.md` | 仓库基础设施 | 业务规则正文 |

## 三、受控例外与白名单

### 1. `tools/`

- `tools/` 是 compatibility shim，不是 `toolchain/` 的第二源码层。
- 只允许保留：
  - `tools/closeout_acceptance_gate.py`
  - `tools/gate_status_backfill.py`
  - `tools/scope_gate_check.py`
- 真逻辑必须在 `toolchain/scripts/test/`。

### 2. `.serena/`

- `.serena/` 属于 repo-local state/config。
- 允许 tracked 白名单：
  - `.serena/.gitignore`
  - `.serena/project.yml`
  - `.serena/memories/Claude-Workspace-Architecture.md`

### 3. `.codex/`

- `.codex/` 属于 repo-local execution config。
- 允许 tracked 白名单：
  - `.codex/config.toml`
  - `.codex/rules/repo.rules`

### 4. `.nav/`

- 只允许 `README.md`、`@docs`、`@skills`。
- `@docs` 与 `@skills` 必须是 symlink。
- `@docs` 必须解析到 `docs/`。
- `@skills` 必须解析到 `product/memory-side/skills/`。

### 5. `.pytest_cache/`

- 可存在于根目录，但不得有 tracked 内容。

## 四、新增根目录对象规则

新增根目录对象前，先回答：

1. 它是不是业务代码？
2. 它是不是仓库真相文档？
3. 它是不是辅助工具或评测资产？
4. 它是不是本地挂载点或运行状态？
5. 它是不是兼容导航或基础设施？

只有能稳定落在上述某一层，才应放到根目录。

## 五、相关文档

- [AGENTS.md](../../../AGENTS.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [Memory Side 层级边界](../../deployable-skills/memory-side/layer-boundary.md)
