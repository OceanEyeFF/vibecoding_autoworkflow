---
title: "Docs 文档治理基线"
status: active
updated: 2026-04-08
owner: aw-kernel
last_verified: 2026-04-08
---
# Docs 文档治理基线

> 目的：在 `docs/` 经历多轮提交后，把入口、层级、状态字段、研究准入与升格规则重新写死，避免同一主题在不同层里重复发声，或者让研究记录误冒充主线真相。

## 一、适用范围

本页只治理 `docs/` 这棵树：

- 入口页如何承担导航
- 正文文档如何声明 owner 和状态
- `analysis` 里的阶段性固定，什么时候只是研究边界，什么时候必须升格到主线

它不替代下面这些合同：

- 根目录边界：见 [根目录分层](./root-directory-layering.md)
- AI 默认阅读顺序：见 [路径治理与 AI 告知](./path-governance-ai-routing.md)
- `product/` 与 `toolchain/` 的源码和工具落点：见 [Toolchain 分层](./toolchain-layering.md)

## 二、治理目标

文档治理至少要保证四件事成立：

1. AI 能先找到稳定入口，而不是从历史残片开始盲读。
2. 同一条规则只有一个主声明位，不在多个目录里平行竞争。
3. 研究阶段可以固定边界，但不会自动升级成当前仓库主线真相。
4. 文档新增后，最近入口页和最小检查脚本会同步更新，而不是只靠人工记忆。

## 三、两类文档对象

### 1. 入口页

当前主要指：

- `docs/README.md`
- `docs/knowledge/README.md`
- `docs/*/README.md`

职责：

- 说明目录语义
- 提供阅读顺序
- 链接当前主线文档

限制：

- 不承担独占性的规则正文
- 不复制叶子文档的完整内容
- 当前仓库允许入口页不写 frontmatter

### 2. 正文文档

指 `docs/` 下除 `README.md` 之外的 markdown 文档。

硬要求：

- 必须有 frontmatter
- 必须至少包含：
  - `title`
  - `status`
  - `updated`
  - `owner`
  - `last_verified`
- 必须有清晰单一作用域，不与同层其他文档重复争夺同一结论

## 四、状态语义

正文文档的 `status` 至少按下面语义使用：

- `active`
  - 当前有效，允许出现在默认入口或当前执行清单中。
- `draft`
  - 仍在整理或待验证，可以被引用，但不应冒充已验证主线。
- `superseded`
  - 已被更新文档、已完成任务或更窄规划替代；允许保留作 lineage，但必须移出默认当前入口。
- `reference`
  - 只用于 `docs/reference/`，表示外部参考，不参与主线断言。

对执行规划类文档额外要求：

- task-plan 或 batch-plan 一旦完成、被替换或不再驱动当前施工，必须改成 `status: superseded`
- `superseded` 规划文档必须保留去向说明，指出当前承接文档或仅说明“保留为 lineage”
- `docs/operations/README.md` 只默认暴露当前仍有效的 runbook 与 research contracts，不把 `superseded` 文档混进“当前状态”

补充限制：

- `suspended` 不是 `docs/` 的长期文档状态，只能视为临时过程标签，不应出现在受治理的正文 frontmatter 中。
- 暂停但仍需共享保留的文档，应改成 `status: superseded` 并退出默认入口。
- 只用于 skill 调用过程、个人备忘或 scratch 工作面的暂停草稿，不应长期留在 `docs/`，应移到 repo-local ignored workspace，而不是继续占据共享文档层。

## 五、层级语义

### 1. `docs/knowledge/`

- 当前有效的 canonical truth
- 适合放稳定规则、分层合同、主线边界

补充：Skills 相关的 contract / canonical / wrapper / templates 边界

- `docs/knowledge/*/skills/` 只定义技能职责、边界、输入输出、格式、reading policy
- `product/*/skills/` 只定义 canonical skill 语义、最小 workflow、references
- `product/*/adapters/*/skills/` 只保留指针、后端 metadata 与最小差异说明
- `docs/knowledge/*/prompts/` 可以承载语义化 prompt 合同，但不应混成 repo-local execution template
- `docs/operations/prompt-templates/` 只作为 `product/harness-operations/` 的 compatibility shim / usage bridge，不定义主线 truth
- 任何需要稳定成为主线 truth 的 prompt-like 内容，都必须先或同步落到 `docs/knowledge/`

### 2. `docs/operations/`

- 当前仓库的 repo-local runbook
- 适合放 CLI 用法、部署帮助、维护步骤

补充：`docs/operations/prompt-templates/` 的治理规则

- 只承接 compatibility shim，不承载主线真相或 canonical prompt body
- 它和 `docs/operations/memory-side/`、`docs/operations/task-interface/` 一起形成 `docs/operations/` 下的稳定路径簇：一个放 deploy / verify / maintenance，一个放 compatibility prompt shims，一个放 partition-specific usage help
- 每个 shim 必须在“相关文档”中回链到对应 `docs/knowledge/` 主线入口与 `product/harness-operations/` canonical source
- 如果 Harness Operations 语义变化，必须先或同步改 `product/harness-operations/`，不得只改 shim
- shim 映射变更后需同步更新 `docs/operations/README.md` 与 `docs/operations/prompt-templates/README.md` 的入口列表

### 3. `docs/reference/`

- 受治理的外部参考
- 只做参考，不做当前仓库主线判断

## 六、研究固定与主线升格

研究类文档允许写“阶段性固定”，但必须区分它固定的到底是什么层级。

### 1. 在 `docs/operations/` 中允许固定的内容

- 某条研究轨道的 phase boundary
- 某个 runner / eval / observability 的当前研究 contract
- 某个尚未进入主线的实验控制模型

这类“固定”表示：

- 对当前研究轨道和当前阶段有效
- 为后续实现和准入提供统一讨论基线

它不表示：

- 已经成为 `docs/knowledge/` 主线规则
- 已经成为 `docs/operations/` 的 repo-local runbook
- 已经替代 `product/` 或 `toolchain/` 的真实实现合同

### 2. 升格规则

当研究结论被接受时，必须把结论写入承接层：

1. 稳定规则、边界和命名：写入 `docs/knowledge/`
2. repo-local 使用步骤和维护方法：写入 `docs/operations/`
3. 已经落地的脚本或源码 contract：落实到 `toolchain/`、`product/` 及其入口文档
4. 原始研究规划文档保留为研究记录，并回链到已承接的主线文档

禁止只让主线结论停留在临时规划文档中。

### 3. 当前 autoresearch 三份文档的定位

当前这三份文档：

- `docs/operations/research-eval-contracts.md`
- `docs/operations/research-eval-observability.md`
- `docs/operations/autoresearch-next-stage-cli-modularity-plan.md`

固定的是 `autoresearch` 轨道的 P0 分阶段边界：

- P0.1：contract、suite 分层、scoreboard、`history.tsv` 初始列
- P0.2：champion/candidate worktree 生命周期和 promote/discard 语义
- P0.3：baseline loop、round 目录、mutation spec 和 keep/discard 的最小规则

这三份文档当前属于“研究轨道的阶段合同/规划入口”，不是自动覆盖全仓库主线的正式规则。

## 七、新增或修改文档时的最小动作

每次往 `docs/` 新增或显著修改文档，至少完成下面动作：

1. 先确定它属于 `knowledge / operations / reference` 的哪一层。
2. 如果是正文文档，补齐 frontmatter。
3. 更新最近的入口页，至少让同目录 `README.md` 能找到它。
4. 如果它属于主线知识目录，优先接到 `docs/knowledge/README.md` 或对应子目录 `README.md`。
5. 如果新文档接管了旧作用域，补回链或退役旧文档，避免双份主线。
6. 如果结论已经准入主线，不要只改临时规划文档，要同步改承接层。
7. 如果执行规划已经完成或被替换，把旧规划改成 `status: superseded`，并从默认当前入口移走。
8. 如果文档当前只是暂停中的草稿或中间笔记，不要发明 `suspended` 长期状态；共享保留则转 `superseded`，非共享草稿则移出 `docs/`。

## 八、当前最小自动检查

当前轻量治理检查至少覆盖：

- markdown 相对链接可达
- 关键入口页存在
- `knowledge` 主线入口存在且能继续回链到主要子入口
- `path-governance` 与 `docs-governance` 的关键回链存在
- 正文文档 frontmatter 齐全
- `status` 与目录语义和生命周期规则一致
- `docs/operations/README.md` 与 `docs/knowledge/autoresearch/README.md` 能维持 research/runbook 分流

当前运行入口见：

- [路径与文档治理检查运行说明](../../operations/path-governance-checks.md)

## 九、相关文档

- [Docs 模块入口](../../README.md)
- [路径治理与 AI 告知](./path-governance-ai-routing.md)
- [根目录分层](./root-directory-layering.md)
- [Toolchain 分层](./toolchain-layering.md)
