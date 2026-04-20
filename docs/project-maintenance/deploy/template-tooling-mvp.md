---
title: "Template Tooling MVP"
status: active
updated: 2026-04-20
owner: aw-kernel
last_verified: 2026-04-20
---
# Template Tooling MVP

> 目的：为 B2（Template Tooling 第二阶段）提供一个最小可执行工作面，只负责把 `product/.aw_template/` 渲染成 `.aw/` 运行样例，并在生成前检查源模板的基本完整性。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Template Consumption Spec](./template-consumption-spec.md)
- [First-Wave Skill Freeze](./first-wave-skill-freeze.md)

## 一、范围

当前 B2 只承接下面三件事：

- 从 `product/.aw_template/` 读取源模板并生成 `.aw/` 运行样例文件
- 给生成结果补充最小 provenance（来源追溯）frontmatter（来源头信息），并对未提供值的关键字段写入非空 placeholder（占位值）
- 对源模板做最小结构校验，避免空字段、缺 section（章节） 或缺关键 keyed field（键值字段）

当前 `.aw/` 样板与 canonical artifact contract 的最低对齐面至少包括：

- `worktrack/contract.md` 要带上 `Constraints` 与 `Verification Requirements`
- `worktrack/plan-task-queue.md` 要显式暴露 `selected_next_action_id` 与 dispatch handoff packet
- `worktrack/gate-evidence.md` 要按 review / validation / policy lane 提供 freshness、confidence 与 route decision

当前 B2 不承接：

- payload descriptor 消费
- `adapter payload` 生成
- deploy target（部署目标） 同步
- backend-specific（后端专属） wrapper（封装层）
- 全 skill 树（skill 的层级依赖结构）通用 orchestrator（编排器）
- `gate`（阶段准入）/ `recover`（异常恢复）/ `closeout`（收尾关闭）的完整生命周期初始化

## 二、工具入口

当前工具入口固定为：

- `toolchain/scripts/deploy/aw_scaffold.py`

支持 3 个子命令：

- `list`
  - 列出当前所有可用的 profile（模板集合，即一组需要一起生成的模板配置）及其包含的 template id（模板标识）
- `validate`
  - 校验所选 `.aw_template` 源文件是否仍满足 B2 需要的最小结构
- `generate`
  - 将所选模板渲染到指定输出根目录，例如 `/tmp/demo-aw` 或仓库内 `.aw/`

## 三、首发 profile

当前只固定 1 个首发 profile：

- `first-wave-minimal`

它只生成首发链路真正需要的最小 `.aw/` 样例：

- `control-state.md`
- `goal-charter.md`
- `repo/snapshot-status.md`
- `worktrack/contract.md`
- `worktrack/plan-task-queue.md`

`worktrack/gate-evidence.md` 当前不属于首发 profile，但仍可通过单独的 `--template worktrack-gate-evidence` 渲染，用于受控补充或后续测试。

## 四、frontmatter 与 placeholder 规则

### 1. 生成头信息

每个生成文件会在正文前补最小 frontmatter：

- `title`
- `artifact_type`
- `generated_from`
- `updated`
- `owner`

这组 frontmatter 只服务于 B2 的生成追踪，并不等同于 `docs/` 目录下作为权威来源的 frontmatter 规范，也不表示 `.aw/` 文档会被提升为长期维护的知识文档。

### 2. 非空占位策略

当前生成器不允许把已定义的关键字段留空；若调用方未提供值，则写入占位符。

如果调用方没有传入某个上下文值，生成器会写入可见 placeholder，例如：

- `TODO(worktrack_id)`
- `TODO(baseline_branch)`
- `TODO(current_next_action)`

这样做的目的只有两个：

- 让生成样例可直接被人类补全，而不是留下空壳
- 让后续校验能区分"未填写但位置存在"和"字段直接丢失"

### 3. 链接字段

`control-state.md` 中指向其他正式文档的链接字段（即 `control-state` 中通过字段引用的其他 `.aw/` 文档）遵守下面规则：

- 如果本次 profile / template 也会生成对应文件，则写相对路径
- 如果本次没有生成对应文件，则保留 placeholder

因此首发 profile 下：

- `repo_snapshot`
- `worktrack_contract`
- `plan_task_queue`

这些字段会写成指向对应生成文件的相对路径；

- `gate_evidence`

仍保留 placeholder。

## 五、validate 检查什么

`validate` 当前只检查源模板最小结构，不对语义正确性做深推断。

最小检查项包括：

- 模板文件存在
- H1 标题与当前模板契约一致
- 必需 section 存在
- 必需 keyed field 存在

它的目标不是替代 C1 的结构测试，而是给 B2 提供一个足够轻的本地前置检查面。

## 六、推荐命令

先看当前 profile 和 template：

```bash
python3 toolchain/scripts/deploy/aw_scaffold.py list
```

校验当前模板结构：

```bash
python3 toolchain/scripts/deploy/aw_scaffold.py validate --profile first-wave-minimal
```

在临时目录生成首发 `.aw/` 样例：

```bash
python3 toolchain/scripts/deploy/aw_scaffold.py generate \
  --profile first-wave-minimal \
  --output-root /tmp/demo-aw \
  --repo vibecoding_autoworkflow \
  --owner aw-kernel \
  --baseline-branch main \
  --worktrack-id wt-demo \
  --branch feat/wt-demo
```

单独生成非首发的 `gate-evidence` 样例：

```bash
python3 toolchain/scripts/deploy/aw_scaffold.py generate \
  --template worktrack-gate-evidence \
  --output-root /tmp/demo-aw
```

## 七、验收标准

当前 B2 可认为达标，当下面几项成立：

- 能在自定义输出根目录生成首发 `.aw/` 最小样例
- 生成结果具有非空 frontmatter 与 placeholder
- 当源模板缺少必需 section 或必需 keyed field 时，`validate` 能失败并在 stderr 或输出报告中指出具体缺失项
- 工具不消费 payload descriptor，不触碰 `adapter payload` 或 deploy target

## 八、后续边界

以下内容继续留给后续任务包：

- C1：把 B2 的结构检查扩成更完整的 template regression（模板回归） 测试面
- B3：把 canonical skill source（规范 skill 来源） 映射到 `agents` payload（向 AI Agent 发送的请求数据体）
- B4：把 deploy / verify 真正接上 mapping + payload
