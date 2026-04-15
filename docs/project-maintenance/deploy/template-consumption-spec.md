---
title: "Template Consumption Spec"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Template Consumption Spec

> 目的：定义 `product/.aw_template/` 的消费约定，只回答"谁生成、谁消费、何时可回写"，不涉及模板生成脚本或部署行为的具体实现。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先了解以下背景：

- [Deploy Mapping Spec](./deploy-mapping-spec.md) —— 部署映射规范
- [Skill 生命周期维护](./skill-lifecycle.md)
- [根目录分层](../foundations/root-directory-layering.md)

## 一、范围

本规范只定义 `.aw_template/` 的消费边界：

- 每个模板对应什么产物类型
- 谁生成
- 谁消费
- 生命周期是什么
- 建议落点在哪一层
- 是否允许回写文档真相（docs truth）

> **文档真相（docs truth）**：指经过确认、可长期作为稳定依据的正式文档内容。

本规范不定义：

- 模板生成脚本
- `adapter_deploy.py` 的实现
- manifest schema
- backend 扩展
- deploy payload 分发逻辑
- `docs/harness/` 的产物分类体系

## 二、术语

- **定义型产物（truth artifact）**
  - 可作为正式定义的对象
  - 可以升格为文档真相
  - 允许成为后续流程的稳定基线
- **状态型产物（state artifact）**
  - 记录当前运行状态、执行队列或裁决证据
  - 只表达运行时的真实状态
  - 不自动升格为文档真相
- **运行时输入样例（runtime input sample）**
  - 仅用于测试、fixture、smoke 或一次性输入样例
  - 不承担正式定义职责
  - 不应被误写成长期状态或固定信条

## 三、总原则

固定边界如下：

- `.aw_template/` 是仓库本地的执行模板层，不是规范真相（canonical truth）
- `.aw_template/` 不是部署来源
- `.aw_template/` 不直接参与 A1 的部署包分发链
- A1 只允许在边界说明或 `template_inputs` 引用面提及 `.aw_template/`
- 后续 B2 可以据此生成模板实例，但本规范不设计脚本

## 四、模板映射

### 1. `product/.aw_template/control/control-state.template.md`

- 产物类型：状态型产物
- 生成者：supervisor 或当前控制回合的操作者
- 消费者：supervisor、verify、后续控制动作
- 生命周期：随控制面状态变化反复更新，旧值只保留为运行过程记录
- 建议落点：仓库本地控制状态层，作为当前回合的运行态文件
- 是否允许回写文档真相：不允许直接回写；只能在后续验证后由上游正式文档抽取稳定结论

说明：

- 该模板只维护控制面状态
- 其中内容不应承载业务真相正文

### 2. `product/.aw_template/worktrack/contract.template.md`

- 产物类型：定义型产物
- 生成者：worktrack owner 或 task refiner
- 消费者：Harness、context routing、plan 生成、writeback 流程
- 生命周期：每个 worktrack 先定稿，再作为稳定基线使用
- 建议落点：worktrack 正式合同层，最终应能升格为文档真相
- 是否允许回写文档真相：允许，且应作为可升格对象处理

说明：

- 该模板对应的内容应与正式定义保持一致
- 这是 `.aw_template/` 中唯一明确允许升格为文档真相的首发对象

### 3. `product/.aw_template/worktrack/plan-task-queue.template.md`

- 产物类型：状态型产物
- 生成者：executor 或 worktrack owner
- 消费者：runner、operator、gate
- 生命周期：每轮执行前后都可重排、重写或重标记
- 建议落点：当前 worktrack 的执行队列层
- 是否允许回写文档真相：不允许直接回写；只作为运行时的真实状态

说明：

- 该模板用于把 contract 展开成执行顺序
- 其内容会随执行进展变化，不应被当成长期定义

### 4. `product/.aw_template/worktrack/gate-evidence.template.md`

- 产物类型：状态型产物
- 生成者：verifier 或 reviewer
- 消费者：review、closeout、writeback
- 生命周期：每个 gate round 生成或追加，作为裁决证据留存
- 建议落点：gate 证据层或当前 worktrack 的审查记录层
- 是否允许回写文档真相：不允许直接回写；只作为运行时的真实状态

说明：

- 该模板记录证据与裁决依据
- 它支持后续复核，但不自动成为固定信条

## 五、运行时输入样例

运行时输入样例是保留类，不强行映射现有四个模板。

当前结论：

- 这四个模板都不应被默认视为运行时输入样例
- 若后续出现一次性测试样例，应单独定义其生命周期和落点

## 六、与 A1 的关系

与 [Deploy Mapping Spec](./deploy-mapping-spec.md) 的关系只允许是以下两种：

- 作为边界说明，明确 `.aw_template/` 不参与部署包分发
- 作为 `template_inputs` 引用面，描述某个 skill 依赖哪些模板类型

禁止把 A2 写成：

- deploy source 设计
- manifest schema 设计
- backend payload 设计
- 模板生成脚本设计

## 七、验收标准

后续实现至少应满足：

- 四个首发模板都有明确的产物分类
- `contract.template.md` 可升格为文档真相
- 其余三项只保留运行时的真实状态
- `.aw_template/` 不被误写成规范真相或部署来源
- B2 可以在不重写合同的前提下开始设计模板生成
