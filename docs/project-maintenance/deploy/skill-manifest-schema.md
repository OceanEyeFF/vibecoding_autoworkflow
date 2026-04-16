---
title: "Skill Manifest Schema"
status: active
updated: 2026-04-16
owner: aw-kernel
last_verified: 2026-04-16
---
# Skill Manifest Schema

> 目的：为 B1 固定一个过渡性的 `skill manifest` 读取面。它只承接首发 canonical read surface（规范读取面）与首发冻结子路径，不将自身定义为 A1 最终 `manifest` 的完整落地，也不提前预设第二层 truth 或 B3/B4 的实现细节。

本文档代号说明：

- A1：[Deploy Mapping Spec](./deploy-mapping-spec.md)
- A2：[Template Consumption Spec](./template-consumption-spec.md)
- A3：[First-Wave Skill Freeze](./first-wave-skill-freeze.md)
- B1：本规范（`skill manifest` 读取面）
- B2：模板初始化工具（后续实现）
- B3：`payload` source 结构（后续实现）
- B4：deploy / verify 执行（后续实现）

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先看：

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Template Consumption Spec](./template-consumption-spec.md)
- [First-Wave Skill Freeze](./first-wave-skill-freeze.md)

## 一、范围

本规范只回答以下问题：

- B1 阶段的 `skill manifest` 最小字段是什么
- 这些字段如何指向 canonical source 与 backend target 的最小映射
- 哪些信息当前明确不能写进 `manifest`

本规范不定义：

- `backend payload source`（后端载荷来源）的目录形态
- `required payload files`、`payload policy` 与 `reference distribution`（引用分发包）的最终字段形态
- adapter / deploy 工具的具体实现逻辑
- `repo-local`（仓库本地）/ `global`（全局）`target root`（目标根目录）的绝对落点
- `runtime state`（运行时状态）、安装结果或内容哈希
- B2 模板初始化工具
- B3 `payload` source 结构
- B4 deploy / verify 的执行细节

## 二、与 A1 / A2 / A3 的关系

本页必须与现有三条上游边界保持一致：

- A1：[Deploy Mapping Spec](./deploy-mapping-spec.md)
  - 本页只落地一个过渡性的 canonical read-surface manifest（规范读取面清单）子层。
  - A1 中要求最终 `manifest` 承接的 `required payload files`、`payload policy` 与 `reference distribution`（引用分发包），当前仍留给后续 `manifest` revision；B1 不声称已一次性确定 A1 的最终 `manifest` 形态。
  - 因此，B1 不是 A1 最终 `manifest` 的完整落地，仅作为后续 B3 / B4 可扩展的最小前置读取面。
- A2：[Template Consumption Spec](./template-consumption-spec.md)
  - 模板初始化相关路径不进入 `skill manifest`，也不作为 `canonical source`、`payload source` 或 `target owner` 写入本页。
  - 模板初始化仍由后续 B2 负责。
- A3：[First-Wave Skill Freeze](./first-wave-skill-freeze.md)
  - B1 当前只为五个首发 skills 建立实例：
    - `harness-skill`
    - `repo-status-skill`
    - `repo-whats-next-skill`
    - `init-worktrack-skill`
    - `dispatch-skills`
  - 其余 skills 不因目录已存在而自动纳入本轮 `manifest` 范围。

因此，B1 仍处在 B3 / B4 之前：此时只固定清单读取面，不声称 payload 或 deploy/verify 已经实现。

## 三、存放位置

分工固定如下：

- 面向运维人员的 schema 规范（operator-facing schema spec）：
  - `docs/project-maintenance/deploy/skill-manifest-schema.md`
- 机器可读的 schema（machine-readable schema）：
  - `product/harness/manifests/schema/skill-manifest.v1.schema.json`
- 机器可读的实例（machine-readable instances）：
  - `product/harness/manifests/agents/skills/*.json`

这里的 `manifest` 只承接“读取面”，不承接 skill 正文、workflow 正文或 deploy 运行状态。

## 四、最小字段

每份 B1 `skill manifest` 只允许包含以下字段：

### 1. `manifest_version`

- 固定当前 schema 版本
- B1 取值固定为 `skill-manifest.v1`

### 2. `backend`

- 标识该清单实例属于哪个 backend 命名空间
- B1 当前实例只使用 `agents`

### 3. `skill_id`

- 对应 `canonical skill`（规范 skill） 的稳定标识
- 在 B1 清单编写阶段，应与 `canonical skill` 目录的 slug（短标识） 保持一致
- v1 machine schema 当前不对 `skill_id` 与 `canonical_dir` / `target_dir` 进行跨字段一致性校验

### 4. `canonical_dir`

- 仓库内 `canonical source`（规范来源） 的相对目录
- v1 machine schema 仅校验其格式为 `product/harness/skills/<slug>`
- 是否与 `skill_id` 指向同一 slug，当前仍属于 B1 的清单编写与人工审阅（manifest authoring / review）规则
- 这是权威来源目录，不是 deploy target

### 5. `entrypoint`

- 相对 `canonical_dir` 的最小读取入口
- 只用于指出“从哪里开始读”（即读取入口）
- 不复制 `SKILL.md` 正文到 `manifest`

### 6. `included_paths`

- 相对 `canonical_dir` 的最小文件集合
- 只列出后续 payload / deploy 读取面必须追踪的 canonical 文件
- 不把 skill 正文摘要、workflow 展开或 docs 内容复制进清单

### 7. `target_dir`

- 相对 `backend target root`（后端目标根目录） 的目标目录
- 仅表达 backend root 下的相对落点，例如 `skills/<skill_id>`
- 不编码 `repo-local`（仓库本地） 或 `global`（全局） 的绝对根目录

### 8. `first_wave_profile`

- 标识该实例属于哪一组首发冻结约束
- B1 当前固定为 `a3-first-wave`
- 这是对 A3 的 machine-readable（机器可读的） 投影，即供程序解析的映射表达，不替代 A3 正文

### 9. `first_wave_scope_kind`

- 标识该实例在 A3 首发范围内是“整 skill 纳入”还是“只纳入冻结子集”
- 当前只允许：
  - `full-skill`（完整纳入）
  - `subset-by-a3-freeze`（仅纳入 A3 冻结子集）
- 它仅提供机器可读的范围信号，不定义新的 workflow 名称

### 10. `supported_repo_actions`

- 只在上游 `canonical contract`（规范契约，即上游已约定的接口协议） 已经给出明确动作名时使用
- B1 当前仅用于 `repo-whats-next-skill`
- 当前允许的动作名直接复用 canonical / A3 已出现的名字，例如：
  - `enter-worktrack`
  - `hold-and-observe`
- 不允许为其他 skill 人为定义新的 route token（路由标识/动作标识）

## 五、字段约束

### 1. 路径约束

- `canonical_dir` 必须是仓库内 `canonical source`（规范来源） 的相对路径
- `entrypoint` 与 `included_paths` 必须相对 `canonical_dir`
- `target_dir` 必须相对 `backend target root`（后端目标根目录）
- 这些路径都不应包含绝对根目录
- v1 machine schema 会拒绝 `entrypoint`、`included_paths` 与 `target_dir` 中的 `.` / `..` 路径段（path segment），因此不能通过点段（dot segment） 跳出各自声明的相对根目录

### 2. 字段耦合约束

- v1 machine schema 当前仅分别校验 `skill_id`、`canonical_dir` 与 `target_dir` 的独立格式
- `skill_id`、`canonical_dir` 的末段与 `target_dir` 的末段应保持一致，这仍属于 B1 的清单编写与人工审阅（manifest authoring / review）规则
- `entrypoint` 必须同时出现在 `included_paths` 中，这也属于 B1 的清单编写与人工审阅规则
- B1 通过专门的 manifest contract test（清单契约测试） 锁定这些语义关系，但不将其强制写入 v1 JSON Schema

### 3. truth boundary（真值边界） 约束

- `manifest` 不复制 `SKILL.md` 正文
- `manifest` 不复制 workflow body（工作流主体）、prompt body（提示词主体） 或 docs 摘要
- `canonical truth`（规范真值，即权威数据来源） 仍在 `product/harness/skills/`

### 4. runtime/state 约束

当前明确禁止写入：

- install status（安装状态）
- deploy success / failure state（部署成功/失败状态）
- runtime state（运行时状态）
- content hash（内容哈希）
- checksum（校验和）
- absolute target root（绝对目标根目录）
- generated payload path（生成的载荷路径）

### 5. backend 边界

- B1 当前仅生成 `agents` 的实例文件
- 不提前声明不存在的 adapter payload 路径
- `claude` 等后续 backend 如需接入，应在后续任务包新增实例，不将本页回写为“已实现”状态

### 6. 首发冻结投影约束

- `first_wave_profile` 当前固定为 `a3-first-wave`
- `first_wave_scope_kind` 仅表达“整 skill 纳入”或“受 A3 冻结收窄”的机器可读信号
- 如果上游 `canonical contract`（规范契约） 已给出明确动作名，可以再用 `supported_repo_actions` 之类的字段投影该子集
- 如果上游没有给出明确动作名，B1 不应凭空定义新的 route token（路由标识）；此时仅保留 `subset-by-a3-freeze` 的机器可读信号，具体细节仍回到 A3 正文解释
- 这组字段的作用是为后续 B3 / B4 消费方（consumer） 保留冻结信号，而非重写 `canonical skill` 合同

## 六、首发实例约束

当前 B1 仅建立五个首发实例，并保持最小的 included set（纳入集合）：

- `harness-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `init-worktrack-skill`
- `dispatch-skills`

实例编写原则：

- `entrypoint` 指向 skill 当前约定的首读入口
- `included_paths` 只覆盖后续读取面当前已经存在、且与首发链路直接相关的 canonical 文件
- `first_wave_scope_kind` 与 `supported_repo_actions` 只投影 A3 / canonical 已有名字，不额外定义新的 route token（路由标识）
- 不因目录下存在模板、草稿或未来扩展文件，而默认全部纳入

## 七、验收标准

B1 完成后，至少应满足：

- 面向运维人员的 schema 规范（operator-facing schema spec） 已明确区分机器强制执行（machine-enforced） 的约束与当前仍依赖清单编写与人工审阅（manifest authoring / review） 的约束
- 五个首发 skills 均具有唯一、稳定、可机器读取的 `manifest`
- `manifest` 仅表达最小映射，不形成第二层 skill truth（skill 真值）
- 文档须明确说明当前阶段仍早于 B3 payload 与 B4 deploy / verify 的实现

## 八、相关文件

- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Template Consumption Spec](./template-consumption-spec.md)
- [First-Wave Skill Freeze](./first-wave-skill-freeze.md)
- [Harness Manifests README](../../../product/harness/manifests/README.md)
