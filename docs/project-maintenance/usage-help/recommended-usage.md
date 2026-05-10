---
title: "Recommended Harness Usage"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---
# Recommended Harness Usage

> 本文档面向不同使用场景，提供从识别场景到完成操作的完整路径。先判断你的场景，再按对应步骤操作。

## 场景速查

| 场景 | 适用条件 | 参考章节 |
|------|---------|---------|
| 新仓库，无 `.aw/`，想直接使用 Skills | 刚安装完，目标仓库还没有 `.aw/` 目录 | [场景一](#场景一在未初始化-aw-的仓库使用-skills) |
| 已安装 Skills，需要设定项目目标 | `.aw/` 已就绪，想定义第一个 Goal Charter | [场景二](#场景二设置仓库目标) |
| 已有目标，需要追加新功能或调整方向 | 现有 Goal Charter 需要修改或扩展 | [场景三](#场景三变更仓库目标) |
| 已有授权的工作项，需要完整走一个 Worktrack | 已有明确的请求，需要 contract → plan → 执行 → closeout | [场景四](#场景四完整-worktrack-闭环) |

---

## 场景一：在未初始化 `.aw/` 的仓库使用 Skills

> 摘要：安装 Harness Skills → 初始化 `.aw/` 控制面 → 验证 → 进入观察循环，三步走完即可接收第一个 worktrack。

**识别条件**：目标仓库没有 `.aw/` 目录（或不确定是否已初始化）。

### 1. 安装 Harness Skills

如果尚未安装，在目标仓库根目录运行：

```bash
# 先只读诊断
npx aw-installer diagnose --backend agents --json

# 安装
npx aw-installer install --backend agents

# 验证
npx aw-installer verify --backend agents
```

其他 backend 使用对应 `--backend` 参数；Coding CLI 内的 skill 调用示例统一以 Codex 为例。

### 2. 初始化 Harness 控制面

安装完成后，在 Coding CLI 中调用 `set-harness-goal-skill` 初始化 `.aw/`。以 Codex 为例：

```txt
$set-harness-goal-skill 根据当前仓库初始化 Harness 控制面，并生成可确认的 Goal Charter 草稿。
```

按提示输入项目目标。目标应包含：
- 最终要达成的结果（可执行边界）
- 当前非目标和禁止触碰范围
- 可验证的验收标准
- 约束（目录、命令、审批）

### 3. 验证初始化

确认 `.aw/` 目录已创建，包含 `goal-charter.md` 和 `control-state.md`：

```bash
ls -la .aw/
```

### 4. 进入观察循环

```txt
$harness-skill 观察当前仓库状态，准备接收第一个 worktrack 请求。
```

---

## 场景二：设置仓库目标

> 摘要：用 `$set-harness-goal-skill` 写目标描述 → 确认 charter → 用 `$repo-append-request-skill` 发起第一个 worktrack。

**识别条件**：`.aw/` 已初始化，但需要定义或重设项目目标。

### 1. 使用 set-harness-goal-skill

```txt
$set-harness-goal-skill 当前仓库期望最终实现一个 [目标描述]。
```

### 2. 目标描述模板

一个好的目标描述包含：

```txt
项目愿景：一句话说明这个项目最终要做什么

核心目标：
1. [可执行的边界目标]
2. [...]

技术方向：
- [技术选型或架构约束]

非目标：
- [不做什么]

验收标准：
- [可验证的条件1]
- [可验证的条件2]

约束：
- [不可触碰的范围]
```

### 3. 确认目标

目标设定完成后，Harness 创建 `.aw/goal-charter.md`，系统进入 RepoScope.Observe。

### 4. 发起第一个 Worktrack

```txt
$repo-append-request-skill 我想先做 [第一个功能/任务]，范围是 [具体路径]，不做 [排除事项]。
```

Harness 自动分类并进入 worktrack 流程。

---

## 场景三：变更仓库目标

> 摘要：判断变更类型（追加 / 扩张 / 改目标）→ 走对应 skill（`$repo-append-request-skill` 或 `$repo-change-goal-skill`）→ 审批后继续。

**识别条件**：已有 Goal Charter，项目中途需要追加功能或调整方向。

### 1. 判断变更类型

| 变更类型 | 条件 | 操作 |
|---------|------|------|
| 追加新功能（在现有目标内） | 新需求在现有 Goal Charter 范围内 | 用 `$repo-append-request-skill` 分类路由 |
| 范围扩张（当前 worktrack 内追加） | 当前有活跃 worktrack，想增加内容 | 提交 scope expansion 请求，需审批 |
| 目标变更（超出 Goal Charter） | 改变项目愿景/核心目标/系统不变量 | 使用 `$repo-change-goal-skill`，需审批 |

### 2. 追加功能流程

```txt
$repo-append-request-skill 提出你的追加请求。
```

Harness 自动分类路由：**new worktrack**（新建执行）/ **scope expansion**（审批后更新 contract）/ **design-only**（先调研）/ **goal change**（目标变更控制）。

### 3. 变更目标（Goal Change）

修改 Goal Charter 前先确保活跃 worktrack 已 checkpoint 或关闭，然后提交：

```txt
$repo-change-goal-skill 新目标：[描述变更后的目标]；变更理由：[为什么需要变]。
```

等待 programmer 审批，变更完成后系统从 RepoScope.Observe 重新开始。

更详细的变更说明见 [goal-change-guide.md](./goal-change-guide.md)。

---

## 场景四：完整 Worktrack 闭环

> 摘要：提请求（`$repo-append-request-skill`）→ 加入 Worktrack（`$harness-skill`）→ Harness 自动串行执行各 task → 验证 + Gate 裁决 → closeout 提交。有追加需求先做 scope expansion。

**识别条件**：已有明确的工作项，需要走完整流程：append → init → execute → verify → closeout。

### 真实对话示例

**步骤 1-3：提出请求并初始化 Worktrack**

```txt
$repo-append-request-skill 简化 README.md 和文档体系。主要考虑：
1. 主要介绍如何使用 skills
2. aw-installer 仅提供安装方法
3. 不要把内部文档放在对外 README
```

Harness 返回路由分类（new worktrack / docs），确认后：

```txt
$harness-skill 把上述任务加入 Worktrack，追加实现。
```

Harness 自动创建分支、写入 contract（范围/验收标准/约束）、播种计划队列。

**步骤 4-6：执行、验证与提交**

Harness 按依赖顺序串行执行各 task（如 T1 分析 → T2 创建 → T3 重构 → T4 验证 → T5 closeout）。全部完成后自动验证：对照验收标准、检查 link 有效性、frontmatter 合规、无越界写入。Gate 通过后用户输入"允许提交"即完成 closeout。

**步骤 7：Scope Expansion（可选）**

closeout 前需追加任务时：

```txt
$harness-skill 直接把这个任务并入当前的开发 Worktrack，追加实现。
```

Harness 更新 contract 范围、扩展计划队列、执行新任务、二次验证和 closeout。

### 关键原则

- 每个 worktrack 有明确的范围和验收标准
- 不顺手扩边界；新需求走 scope expansion 或 new worktrack
- 只有已验证结果才写入长期真相层
- 提交前等待 programmer 授权

---

## 通用最佳实践

### 安全使用 Harness

1. **先读后写**：`npx aw-installer diagnose --json` 先只读，再 install/update
2. **明确边界**：每个 worktrack contract 声明范围内外、验收标准、约束
3. **控制熵增**：不顺手修相邻问题，相邻风险单独提交请求
4. **验证优先**：文档变更对照验收标准；路径/部署变更跑对应检查脚本
5. **审批边界**：release、publish、远程推送、破坏性操作必须显式授权

### 安全使用 SubAgent

SubAgent 适合限定范围的实现、审查、测试。给 SubAgent 的 prompt 应包含：

- worktrack 目标和非目标
- 允许读写的路径
- 禁止触碰的文件、控制 artifacts、外部动作
- 期望返回的证据格式
- 是否允许运行命令

不要让 SubAgent 自行扩大到 release、publish、全仓重构或 `.aw/` 控制面改写。

### 审批门控清单

以下动作必须有明确审批，不能被普通实现请求或 closeout 暗含授权：

- release、dist-tag、npm/package publish
- 远程推送、开 PR、合并 PR
- destructive reinstall、删除目录、重写历史
- 修改 command semantics 或 runtime adapter 行为
- 改写 `.aw/` 控制 artifacts 或目标契约
