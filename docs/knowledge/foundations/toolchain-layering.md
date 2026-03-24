---
title: "Toolchain 分层"
status: active
updated: 2026-03-25
owner: aw-kernel
last_verified: 2026-03-25
---
# Toolchain 分层

> 目的：把第三块 `toolchain/` 的职责、子目录边界、落点规则和扩展方式固定下来，避免后续继续把“脚本入口”“评测资产”“运行产物”“业务源码”混在一起。

## 一、Toolchain 是什么

`toolchain/` 是当前仓库第三块正式内容区。

它只承载下面这些内容：

- 部署脚本
- 评测程序
- 自动评分规则
- 测试入口
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
- 承接部署、评测执行、评分、打包等动作入口

当前内容：

- `deploy/adapter_deploy.py`
- `research/memory_side_autoresearch.py`
- `research/memory_side_autoresearch_score.py`
- `test/path_governance_check.py`

硬规则：

- `scripts/` 放“动作入口”，不放长期规则正文
- 默认按一个脚本一个明确动作命名
- 输出写到 repo-local state 目录，不写回 `toolchain/`

当前子层级：

- `scripts/deploy/`：部署与安装入口
- `scripts/research/`：评测执行与评分入口
- `scripts/test/`：轻量治理检查入口

### 2. `toolchain/evals/`

职责：

- 保存基础测试提示、问题列表、测试记录格式和测试评分规则

当前内容：

- `fixtures/`
- `memory-side/program.md`
- `memory-side/scenarios.json`
- `memory-side/schemas/`
- `memory-side/scoring/`

其中：

- `fixtures/` 保存跨主题共享的测试仓库说明格式、测试记录格式和少量公共格式说明
- `memory-side/` 保存 `Memory Side` 主题下的基础测试提示、问题列表和测试评分规则

硬规则：

- `evals/` 只保存测量面和评测资产
- 不保存业务源码
- 不保存执行期运行产物

## 三、当前边界规则

### 1. 不该进 `toolchain/` 的东西

下面这些内容不应该继续落到 `toolchain/`：

- `product/` 下的 canonical skill 或 adapter 源码
- `docs/knowledge/` 下的规则正文
- `.agents/`、`.claude/` 下的 repo-local deploy target
- `.autoworkflow/` 下的运行结果

### 2. Toolchain 与其他两块的关系

- `product/` 提供业务源码
- `docs/` 提供知识真相和规则边界
- `toolchain/` 提供执行这些源码与规则所需的工具入口

### 3. 输出落点规则

`toolchain/` 内脚本产生的运行结果，应落到 repo-local state：

- benchmark 运行记录写到 `.autoworkflow/`
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

当前阶段已经落成 `deploy/`、`research/`、`test/` 三类入口。
后续只有在同类工具继续增长时，才继续往下细分。

## 五、命名规则

- 脚本名优先直接表达动作，例如 `adapter_deploy.py`
- 评测目录优先按主题命名，例如 `evals/memory-side/`
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
- [Memory Side 层级边界](../memory-side/layer-boundary.md)
- [Memory Side Repo-local Auto Research Loop](../../analysis/memory-side/memory-side-auto-research-loop.md)
