---
title: "Template Consumption Spec"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Template Consumption Spec

> 目的：重新定义 `product/.aw_template/` 的职责边界。当前它首先是 `.aw/` 运行目录的模板来源，用来生成目录结构和少量直接属于 Harness 运行管理面的文档。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Usage Help](../usage-help/README.md)
- [根目录分层](../foundations/root-directory-layering.md)

## 一、范围

本规范只回答下面几个问题：

- `.aw_template/` 应该用来做什么
- 哪些内容应继续留在 `.aw_template/`
- 哪些内容不该继续留在 `.aw_template/`
- 当前目录里已有模板文件时，暂时该怎么理解
- 在归属方重新确定前，哪些使用方式是允许的

本规范不回答：

- 每个模板最终归哪个 skill
- 模板迁移顺序
- 模板生成脚本
- `adapter_deploy.py` 的实现
- payload descriptor schema
- backend 扩展
- `docs/harness/` 的产物定义体系

## 二、术语

- **`.aw` 运行模板**
  - 用于初始化 `.aw/` 目录结构，或其中直接属于运行管理面的文档
  - 关注的是 `.aw/` 的组织方式和运行时入口，而不是某个 skill 的产物 owner
- **skill 持有模板（skill-owned template）**
  - 由某个 skill 持有，并直接表达该 skill 产物形态的模板
  - 长期应跟随所属 skill，而不是长期留在 `.aw_template/`
- **仅文档定义（docs-only definition）**
  - 只需要由文档层定义结构和约束
  - 不要求在仓库内长期保留一份同名模板文件

## 三、总原则

固定边界如下：

- `.aw_template/` 是仓库本地执行模板层，但它首先服务于 `.aw/`
- `.aw_template/` 不是 canonical truth（规范真相）
- `.aw_template/` 不是 skill deploy source
- `.aw/` 顶层可以保留不属于 `repo/`、`worktrack/` 的直接运行管理文档
- repo 级和 worktrack 级管理文档应在 `.aw/` 下按层级落位
- goal 修正文档不保存在 `.aw/` 路径下，只作为 Codex 对话回答流模板存在
- 明显属于某个 skill 产物的模板，长期应优先归到所属 skill，而不是默认留在 `.aw_template/`

## 四、`.aw_template/` 当前应保留什么

按当前模型，`.aw_template/` 应保留的是下面这些结构位：

- `repo/`
- `worktrack/`
- `template/`
- `control-state.md`
- `goal-charter.md`

其中：

- `control-state.md`
  - 对应 `.aw/` 顶层
  - 原因是它属于 Harness 直接状态管理，不属于 `repo/`，也不属于 `worktrack/`
- `goal-charter.md`
  - 对应 `.aw/` 顶层
  - 原因是它更接近全局常量位，变动频率低，不适合塞进某个分层目录
- `repo/`
  - 用于放 `.aw/repo/` 下的 repo 级管理文档
- `worktrack/`
  - 用于放 `.aw/worktrack/` 下的 worktrack 级管理文档
- `template/`
  - 用于放不直接进入 `.aw/` 路径、但仍需要保留的回答流模板

当前明确保留在 `template/` 下的对象是：

- `goal-charter.template.md`

## 五、哪些内容不该继续长期留在这里

下面这类模板，不应再把 `.aw_template/` 当作长期 owner：

- `contract`
- `plan-task-queue`
- `gate-evidence`
- 其他明显由某个 skill 直接生成、维护、消费的模板

这些对象后续虽然会落到 `.aw/repo/` 或 `.aw/worktrack/`，但它们的模板归属应按 skill 或关联 skill 重新确定。

goal 修正文档单独处理：

- 不保存在 `.aw/` 路径下
- 只作为 Codex 对话回答流模板存在
- 使用时带批准边界

## 六、当前结构怎么理解

当前 `product/.aw_template/` 下保留的是这组 `.aw/` 目录模板来源：

- `control-state.md`
- `goal-charter.md`
- `repo/analysis.md`
- `repo/snapshot-status.md`
- `worktrack/contract.md`
- `worktrack/plan-task-queue.md`
- `worktrack/gate-evidence.md`
- `template/goal-charter.template.md`

同时，已经迁到 skill 一侧的 owner 模板包括：

- `product/harness/skills/repo-change-goal-skill/templates/goal-change-request.template.md`
- `product/harness/skills/init-worktrack-skill/templates/contract.template.md`
- `product/harness/skills/schedule-worktrack-skill/templates/plan-task-queue.template.md`
- `product/harness/skills/gate-skill/templates/gate-evidence.template.md`

当前结论先收敛到三条：

- `.aw_template/` 中保留的是 `.aw/` 目录模板来源，不再把它写成 artifact 模板总仓
- 对于 `contract / plan-task-queue / gate-evidence` 这类对象，`.aw_template/` 负责 `.aw/` 落位模板，skill 包负责 owner 模板
- `goal-change-request` 已经从 `.aw_template/` 移出，不再进入 `.aw/` 路径

## 七、当前允许的使用方式

在归属方重新确定完成前，允许的使用方式只有：

- 将 `.aw_template/` 视为 `.aw/` 模板来源与过渡暂存位
- 将其中现有旧模板视为待迁移库存，而不是最终归属结论
- 在分析和迁移设计中引用这些文件清单

当前不允许的使用方式：

- 把 `.aw_template/` 继续定义成产物模板的长期主目录
- 依据当前路径，直接断言某个模板已经归属某个层或某个 skill
- 把 `.aw_template/` 当作 skill 部署来源
- 在没有重新确定归属方前，继续扩写新的产物模板到这里

## 八、与 A1 的关系

与 [Deploy Mapping Spec](./deploy-mapping-spec.md) 的关系只允许是以下两种：

- 作为边界说明，明确 `.aw_template/` 不参与 skill 部署包分发
- 作为 `.aw/` 模板来源的说明对象，而不是产物归属目录

禁止把本文档（A2）写成：

- 所有模板的最终 skill 归属结论
- 部署来源设计
- payload descriptor 设计
- backend payload 设计
- 模板生成脚本设计

## 九、验收标准

这轮纠偏完成后，至少应满足：

- `.aw_template/` 已被重新定义为 `.aw/` 目录模板来源，而不是产物模板总仓
- `control-state.md` 和 `goal-charter.md` 作为 `.aw/` 顶层管理文档的定位是明确的
- `template/goal-charter.template.md` 作为保留回答流模板的定位是明确的
- goal 修正文档不进入 `.aw/` 路径
- 后续迁移不会再把 `.aw_template` 当前路径当作所有模板的 owner 证明
