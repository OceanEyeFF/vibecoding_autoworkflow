---
title: "根目录分层"
status: active
updated: 2026-04-26
owner: aw-kernel
last_verified: 2026-04-26
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
| Distribution Manifest Layer | `package.json` | npm/npx 分发包络元数据 | 业务源码真相、运行状态 |
| Repo-local Install / Mount Layer | `.claude/` `.agents/` `.opencode/` | repo-local 安装载荷、挂载与 deploy target | 主线真相、业务源码 |
| Repo-local State Layer | `.aw/` `.autoworkflow/` `.spec-workflow/` | 运行状态、Harness 控制面运行产物与项目级配置记忆 | 主线入口、业务源码、长期真相 |
| Repo-local Execution Config Layer | `.codex/` | repo-local 执行配置 | 长期真相正文、运行产物 |
| Compatibility Navigation Layer | `.nav/` | 兼容导航 | 结构定义与规则正文 |
| Compatibility Shim Layer | `tools/` | 兼容入口 shim | canonical 逻辑实现 |
| Local Ephemeral Cache Layer | `.pytest_cache/` | 本地测试缓存 | tracked 主线内容 |
| Repo Infra Layer | `.github/` `.git/` `.gitignore` `.gitattributes` `.claudeignore` `LICENSE` `CONTRIBUTING.md` | 仓库基础设施 | 业务规则正文 |

## 三、受控例外与白名单

### 0. Repo-local deploy targets

- `.agents/skills/`、`.claude/skills/`、`.opencode/skills/` 只承接 repo-local deploy 结果与 operator runtime 挂载。
- 这些目录必须保持 ignored；不得把其中任何内容作为 tracked 主线文件入库。
- 这些目录不是 canonical truth，也不是业务源码根；fresh checkout 不应携带 repo-local deploy target 镜像。
- `product/` 仍然是业务代码唯一源码根；repo-local deploy target 不应反向替代 `product/` 或 `docs/` 的定义权。
- 需要分发或回归验证的 skill 内容必须从 `product/`、`toolchain/` 或正式文档入口承接，而不是跟踪 `.agents/`、`.claude/` 或 `.opencode/` 下的安装结果。

### 1. `tools/`

- `tools/` 是 compatibility shim，不是 `toolchain/` 的第二源码层。
- 只允许保留：
  - `tools/closeout_acceptance_gate.py`
  - `tools/gate_status_backfill.py`
  - `tools/scope_gate_check.py`
- 真逻辑必须在 `toolchain/scripts/test/`。

### 2. `.codex/`

- `.codex/` 属于 repo-local execution config。
- 允许 tracked 白名单：
  - `.codex/config.toml`
  - `.codex/rules/repo.rules`

### 3. `.nav/`

- 只允许 `README.md`、`@docs`、`@skills`。
- `@docs` 与 `@skills` 必须是 symlink。
- `@docs` 必须解析到 `docs/`。
- `@skills` 必须解析到 `product/harness/skills/`。

### 4. `.pytest_cache/`

- 可存在于根目录，但不得有 tracked 内容。

### 5. `.aw/`

- `.aw/` 属于 repo-local Harness runtime control-plane state。
- 它可以在本地存在并被治理检查识别为合法根目录对象，但仍必须保持 ignored，不是长期 truth layer。
- `.aw/` 中的运行合同、队列和 evidence 只用于当前控制回路，不替代 `docs/`、`product/` 或 `toolchain/` 中的正式真相与源码。

### 6. `package.json`

- 根目录 `package.json` 只承接 `aw-installer` 的 npm/npx 分发包络元数据。
- 该 manifest 可以从根目录打包 `product/` 中的 canonical Harness payload 和 `toolchain/scripts/deploy/` 中的 wrapper 工具，但不得把业务源码真相迁出 `product/`。
- 发布动作不属于根目录分层规则本身；是否发布 npm package 必须由 deploy/release 合同另行控制。

## 四、新增根目录对象规则

新增根目录对象前，先回答：

1. 它是不是业务代码？
2. 它是不是仓库真相文档？
3. 它是不是辅助工具或评测资产？
4. 它是不是本地挂载点或运行状态？
5. 它是不是兼容导航或基础设施？

只有能稳定落在上述某一层，才应放到根目录。

## 五、文档域补充

`docs/` 当前一级文档域包括：

- `project-maintenance/`
- `harness/`

其中：

- `docs/harness/` 是 Harness-first 主线

`product/` 当前一级源码根包括：

- `harness/`

`product/` 下还允许一个受控辅助层：

- `.aw_template/`：repo-local execution template layer，用于承接 `.aw/` 运行目录的 scaffold 模板；artifact 模板的长期 owner 不应默认落在这里

## 六、相关文档

- [AGENTS.md](../../../AGENTS.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [Memory Side 层级边界](../../harness/adjacent-systems/memory-side/layer-boundary.md)
