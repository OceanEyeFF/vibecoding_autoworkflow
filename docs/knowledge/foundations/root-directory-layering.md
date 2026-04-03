---
title: "根目录分层"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# 根目录分层

> 目的：把根目录收口成稳定的三大正式内容区，再加少量本地挂载和状态目录，避免继续把“业务源码”“文档真相”“辅助工具”“本地挂载点”混成一层。

## 一、当前正式分层

当前根目录只认这三块正式内容区：

1. `product/`：业务代码唯一源码根
2. `docs/`：仓库文档与知识真相层
3. `toolchain/`：脚本、评测、测试、打包与部署工具

除此之外，根目录只允许保留：

- `.claude/`、`.agents/`、`.opencode/`：repo-local mount / deploy target
- `.autoworkflow/`、`.spec-workflow/`、`.serena/`：repo-local state
- `.codex/`：repo-local execution config layer
- `.nav/`：兼容导航层
- `tools/`：根目录兼容 shim；只保留少量委托到 `toolchain/scripts/test/` 的包装脚本
- `.pytest_cache/`：本地 ephemeral cache，可存在但不得入库
- `.github/`、`.git*`、`LICENSE`、`CONTRIBUTING.md`、`.claudeignore` 等基础设施文件

## 二、根目录层级

| 层级 | 根目录对象 | 职责 | 不应该承载什么 |
|---|---|---|---|
| Entry Layer | `README.md` `INDEX.md` `GUIDE.md` `ROADMAP.md` `AGENTS.md` | 把人或 agent 导向当前主线 | 长期规则正文、repo-local 细节 |
| Product Layer | `product/` | 业务代码唯一源码根 | 仓库真相正文、评测产物、运行状态 |
| Truth Layer | `docs/` | 项目真相、知识基线、研究约束、归档 | 部署结果、本地挂载点、运行状态 |
| Toolchain Layer | `toolchain/` | 脚本、评测、测试、打包、部署工具 | 业务源码真相、repo-local 手工维护 wrapper |
| Repo-local Mount Layer | `.claude/` `.agents/` `.opencode/` | 本地测试挂载点、repo-local deploy target | 业务源码真相、长期规则正文 |
| Repo-local State Layer | `.autoworkflow/` `.spec-workflow/` `.serena/` | 运行产物、审批状态、工具配置与记忆；其中 `.serena/` 可保留受控入库的项目级配置与记忆白名单 | 当前主线入口、业务源码 |
| Repo-local Execution Config Layer | `.codex/` | Codex 的 repo-local 执行配置、规则与默认约束 | 长期真相正文、业务源码、运行产物 |
| Compatibility Navigation Layer | `.nav/` | 辅助导航和兼容跳转 | 主线规则、真实结构定义 |
| Compatibility Shim Layer | `tools/` | 给 legacy gate / harness 保留最小兼容入口，真逻辑仍在 `toolchain/scripts/test/` | canonical 源码、缓存、运行产物 |
| Local Ephemeral Cache Layer | `.pytest_cache/` | 本地测试缓存 | tracked 内容、主线规则 |
| Repo Infra Layer | `.github/` `.git/` `.gitignore` `.gitattributes` `.claudeignore` `LICENSE` `CONTRIBUTING.md` | 版本控制和仓库级基础配置 | 业务规则和知识层内容 |

## 三、三块正式内容区

### 1. `product/`

这是第一块，也是业务代码唯一源码根。

当前主线：

- `product/memory-side/skills/`：canonical skill 源码
- `product/memory-side/adapters/claude/`：Claude adapter 源码
- `product/memory-side/adapters/agents/`：Codex / OpenAI adapter 源码
- `product/memory-side/adapters/opencode/`：OpenCode adapter 源码
- `product/memory-side/manifests/`：全局安装与分发元数据预留位
- `product/task-interface/skills/`：Task Interface canonical skill 源码
- `product/task-interface/adapters/claude/`：Task Interface 的 Claude adapter 源码
- `product/task-interface/adapters/agents/`：Task Interface 的 Codex / OpenAI adapter 源码
- `product/task-interface/adapters/opencode/`：Task Interface 的 OpenCode adapter 源码

硬规则：

- 业务源码只改 `product/`
- `.claude/`、`.agents/` 和 `.opencode/` 里的内容不手工维护
- repo-local wrapper 由部署脚本从 `product/` 同步出来

### 2. `docs/`

这是第二块，承载仓库真相和知识文档。

当前主线入口：

- `docs/README.md`

当前内部层级：

- `docs/knowledge/`：canonical truth 与 foundations
- `docs/operations/`：repo-local runbook
- `docs/analysis/`：benchmark 与研究说明
- `docs/reference/`：外部参考资料
- `docs/ideas/`：未准入主线的 ideas
- `docs/archive/`：退役资料

### 3. `toolchain/`

这是第三块，承载辅助工具和测量资产。

当前主线：

- `toolchain/scripts/`
- `toolchain/evals/`

硬规则：

- `toolchain/` 只放脚本、评测、测试、打包、部署工具
- 不再把 canonical skill 源码继续放在 `toolchain/`

## 四、repo-local mount 层

包括：

- `.claude/`
- `.agents/`
- `.opencode/`

它们现在只承担两类职责：

- 本仓库内快速测试的 mount 目录
- 从 `product/` 一键部署出来的 repo-local 产物

硬规则：

- 必须在 `.gitignore` 中忽略
- 不作为 source of truth
- 不在这里手工维护规则正文

## 五、受控例外与兼容层

### 1. `tools/`

- `tools/` 是根目录 compatibility shim，不是 `toolchain/` 的第二份源码层
- 只允许保留少量 tracked wrapper：
  - `tools/closeout_acceptance_gate.py`
  - `tools/gate_status_backfill.py`
  - `tools/scope_gate_check.py`
- 真逻辑必须继续落在 `toolchain/scripts/test/`

### 2. `.serena/`

- `.serena/` 仍属于 repo-local state/config
- 允许 tracked 的白名单当前固定为：
  - `.serena/.gitignore`
  - `.serena/project.yml`
  - `.serena/memories/Claude-Workspace-Architecture.md`
- 除白名单外，`.serena/` 里的 tracked 内容都视为结构违规

### 3. `.nav/`

- `.nav/` 只允许 `README.md`、`@docs`、`@skills`
- `@docs` 与 `@skills` 必须是 symlink
- `@docs` 必须解析到 `docs/`
- `@skills` 必须解析到 `product/memory-side/skills/`

### 4. `.codex/`

- `.codex/` 仍属于 repo-local execution config layer
- 允许 tracked 的白名单当前固定为：
  - `.codex/config.toml`
  - `.codex/rules/repo.rules`
- 除白名单外，`.codex/` 里的 tracked 内容都视为结构违规
- `.codex/` 不承载长期真相正文，也不承载业务源码

### 5. `.pytest_cache/`

- `.pytest_cache/` 是本地 ephemeral cache
- 可存在于根目录，但不得有 tracked 内容

## 六、根目录放置规则

新增根目录对象前，先回答下面问题：

1. 它是不是业务代码？
2. 它是不是仓库真相文档？
3. 它是不是辅助工具或评测资产？
4. 它是不是本地挂载点或运行状态？
5. 它是不是兼容导航或基础设施？

只有能稳定落到上述某一层，才应该放到根目录。

下面这些理由都不够：

- “先临时放这里”
- “以后可能会有用”
- “只是这个 Prompt 需要一个目录”
- “现在还没想清楚 owner”

## 七、当前收口形态

```text
.
├── README.md
├── INDEX.md
├── GUIDE.md
├── ROADMAP.md
├── AGENTS.md
├── CONTRIBUTING.md
├── .github/            # repo infra (PR/CI)
├── .codex/              # repo-local execution config
├── product/              # 业务代码
├── docs/                 # 文档真相
├── toolchain/            # 脚本、评测、部署工具
├── .claude/              # repo-local mount
├── .agents/              # repo-local mount
├── .opencode/            # repo-local mount
├── .autoworkflow/        # repo-local state
├── .spec-workflow/       # repo-local state
├── .serena/              # repo-local state
├── .nav/                 # compatibility navigation
├── tools/                # compatibility shim
├── .pytest_cache/        # local ephemeral cache
└── repo infra files
```

## 八、当前已知问题

- `.nav/` 仍然带有旧时代导航假设，部分入口只属于兼容层
- `docs/archive/` 和 `docs/ideas/incubating/` 当前仍然很轻，但它们的职责已经明确

## 九、相关文档

- [Docs 模块入口](../../README.md)
- [路径治理与 AI 告知](./path-governance-ai-routing.md)
- [项目 Partition 模型](./partition-model.md)
- [Toolchain 分层](./toolchain-layering.md)
- [Memory Side 层级边界](../memory-side/layer-boundary.md)
- [Memory Side 总览](../memory-side/overview.md)
