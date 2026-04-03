---
title: "Toolchain 分层"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Toolchain 分层

> 目的：把第三块 `toolchain/` 的职责、子目录边界、落点规则和扩展方式固定下来，避免后续继续把“脚本入口”“评测资产”“运行产物”“业务源码”混在一起。

## 一、Toolchain 是什么

`toolchain/` 是当前仓库第三块正式内容区。

它只承载下面这些内容：

- 部署与同步脚本
- 治理检查与 gate 入口
- 已准入的 research runner 与实验 orchestration
- 已准入的 eval / fixture / prompt 资产
- 打包与分发工具

它不承载下面这些内容：

- 业务源码
- 文档真相正文
- repo-local mount
- 运行产物

## 二、当前内部结构

当前主线只有两层：

```text
toolchain/
├── README.md
├── scripts/
└── evals/
```

### 1. `toolchain/scripts/`

职责：

- 提供可直接执行的 CLI 脚本
- 承接部署、治理检查、打包等动作入口

当前内容：

- `deploy/`
- `research/`
- `test/`

说明：

- `deploy/` 当前承接 active 的 deploy / verify / sync 动作入口
- `research/` 当前已经是已准入的 active 研究工具层，承接 runner、autoresearch 外环、backend acceptance 入口与相关实验 orchestration
- `test/` 当前承接轻量治理检查与 closeout gate 等验证入口
- 具体入口和对象说明以下游 README 为准：[`toolchain/scripts/README.md`](../../../toolchain/scripts/README.md)

硬规则：

- `scripts/` 放“动作入口”，不放长期规则正文
- 默认按一个脚本一个明确动作命名
- 输出写到 repo-local state 目录，不写回 `toolchain/`

当前子层级：

- `scripts/deploy/`：部署与同步入口
- `scripts/research/`：已准入的研究 runner 和实验 orchestration
- `scripts/test/`：治理检查、验收 gate 与轻量测试入口

### 2. `toolchain/evals/`

职责：

- 保存被明确准入、可复用的 eval 资产入口
- 为 active runner 提供稳定的 prompt、fixture、schema 与 topic-scoped eval 入口

当前内容：

- `prompts/`
- `fixtures/`
- `memory-side/`

说明：

- `prompts/` 当前承接 repo-local 的 eval prompt 模板
- `fixtures/` 当前承接稳定的 schema 与 suite manifest 等 fixture 资产
- `memory-side/` 当前承接已准入主题的 eval 入口，而不是“未来再定”的纯占位目录
- 具体对象与边界以下游 README 为准：[`toolchain/evals/README.md`](../../../toolchain/evals/README.md)

硬规则：

- `evals/` 只保存测量面和评测资产
- 不保存业务源码
- 不保存执行期运行产物

## 三、当前边界规则

### 1. 不该进 `toolchain/` 的东西

下面这些内容不应该继续落到 `toolchain/`：

- `product/` 下的 canonical skill 或 adapter 源码
- `docs/knowledge/` 下的规则正文
- `.agents/`、`.claude/`、`.opencode/` 下的 repo-local deploy target
- `.autoworkflow/` 下的运行结果

### 2. Toolchain 与其他两块的关系

- `product/` 提供业务源码
- `docs/` 提供知识真相和规则边界
- `toolchain/` 提供执行这些源码与规则所需的工具入口

### 3. 输出落点规则

`toolchain/` 内脚本产生的运行结果，应落到 repo-local state：

- 未来测量脚本的运行记录写到 `.autoworkflow/`
- 其他审批、记忆或状态写到各自状态目录

不要把下面这些东西直接写回 `toolchain/`：

- 运行日志
- 临时结果
- 交互缓存
- 本地用户配置

## 四、扩展规则

当 `toolchain/` 继续增长时，优先按“动作类型”分层，而不是按历史来源堆文件。

推荐扩展顺序：

1. 保持 `scripts/` 和 `evals/` 两大层不变
2. 只有当 `scripts/` 文件明显增多时，再拆子目录：
   - `scripts/deploy/`
   - `scripts/research/`
   - `scripts/package/`
   - `scripts/test/`
3. 只有当测试资产需要独立沉淀时，再新增 `toolchain/tests/`

当前阶段的 active 入口不只包含 `deploy/` 和 `test/`。
`research/` 已经是 active 的研究执行层，`evals/` 也是已准入的稳定评测资产层；后续扩展应继续沿这两个已准入层演进，而不是把它们当成纯预留位。

## 五、命名规则

- 脚本名优先直接表达动作，例如 `adapter_deploy.py`
- 测量目录优先按主题命名，例如 `evals/<topic>/`
- 不使用 `misc`、`temp`、`draft-tools` 这类无 owner 的目录名
- 如果一个新脚本说不清它属于部署、评测、测试还是打包，就不要直接加入 `toolchain/`

## 六、当前判断

按 `2026-03-22` 的状态，第三块已经具备可治理的最小收口：

- `toolchain/scripts/` 负责执行动作
- `toolchain/evals/` 负责稳定测量面
- 业务源码已经不再放在 `toolchain/`

所以第三块现在的重点不是“大迁移”，而是：

- 把边界写死
- 把入口文档回链好
- 后续新增工具时严格按层级收纳

## 七、相关文档

- [根目录分层](./root-directory-layering.md)
- [Scripts 入口总览](../../../toolchain/scripts/README.md)
- [Evals 入口总览](../../../toolchain/evals/README.md)
- [Memory Side 层级边界](../memory-side/layer-boundary.md)
