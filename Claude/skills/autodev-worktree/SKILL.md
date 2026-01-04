---
name: autodev-worktree
description: >
  Git Worktree 并行开发工作流 - 在独立工作树中进行功能开发或实验。
  支持：并行开发多个功能分支、隔离实验性改动、处理代码冲突。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, AskUserQuestion, Task
---

# AutoDev Worktree - Git 并行开发工作流

你现在进入 **Git Worktree 并行开发模式**。这个模式允许在独立的工作目录中进行开发，不影响主工作区。

## 适用场景

1. **并行开发**：同时处理多个功能分支，互不干扰
2. **隔离实验**：在独立目录中进行实验性改动，随时可以丢弃
3. **代码审查**：在保持当前工作的同时，检出 PR 进行审查
4. **热修复**：主分支开发中途，需要紧急修复生产问题

## 核心概念

### 什么是 Git Worktree？

Git Worktree 允许在同一个仓库创建多个工作目录，每个目录可以检出不同的分支。

```
项目结构示例：
my-project/              # 主工作区（main 分支）
├── .git/
├── src/
└── ...

../.worktrees/my-project/
├── feature-a/           # Worktree 1（feature-a 分支）
│   ├── src/
│   └── ...
├── feature-b/           # Worktree 2（feature-b 分支）
│   ├── src/
│   └── ...
└── experiment/          # Worktree 3（实验分支）
    ├── src/
    └── ...
```

## 工作流程

### Phase 1: 创建 Worktree

**目标**：为新功能或实验创建独立的工作目录

**步骤**：

1. **确认需求**
   - 使用 AskUserQuestion 确认：
     - 功能名称/分支名称
     - 基于哪个分支创建（默认：当前分支）
     - 场景类型（功能开发 / 实验 / 热修复）

2. **创建 Worktree**
   ```bash
   # 获取当前仓库名
   basename $(git rev-parse --show-toplevel)

   # 创建 worktree 目录
   # 路径规范：../.worktrees/{项目名}/{分支名}
   git worktree add "../.worktrees/$(basename $(pwd))/{branch-name}" -b {branch-name}
   ```

3. **验证创建成功**
   ```bash
   git worktree list
   ```

4. **输出结果**
   ```
   ## Worktree 创建成功

   **分支**：{branch-name}
   **路径**：../.worktrees/{project}/{branch-name}
   **基于**：{base-branch}

   下一步：
   - 切换到 worktree 目录进行开发
   - 使用 /autodev 开始功能开发
   ```

### Phase 2: 在 Worktree 中开发

**目标**：在独立工作区执行 AutoDev 工作流

**步骤**：

1. **切换到 Worktree 目录**
   ```bash
   cd "../.worktrees/{project}/{branch-name}"
   ```

2. **执行 AutoDev 工作流**
   - 需求理解 → 任务拆分 → 迭代开发 → 验收
   - 所有操作在 worktree 目录内进行

3. **定期同步（可选）**
   ```bash
   # 从主分支拉取更新（如需要）
   git fetch origin
   git merge origin/main  # 或 rebase
   ```

### Phase 3: 合并与清理

**目标**：完成开发后合并代码并清理 Worktree

**步骤**：

1. **提交所有更改**
   ```bash
   git add .
   git commit -m "feat(scope): 完成功能实现"
   git push -u origin {branch-name}
   ```

2. **回到主工作区**
   ```bash
   cd {main-workspace}
   ```

3. **合并分支**（用户确认后）
   ```bash
   git checkout main
   git merge {branch-name}
   # 或创建 PR
   ```

4. **清理 Worktree**
   ```bash
   git worktree remove "../.worktrees/{project}/{branch-name}"
   git branch -d {branch-name}  # 删除本地分支（如已合并）
   ```

## 常用命令参考

### 查看所有 Worktree
```bash
git worktree list
```

### 创建 Worktree（新分支）
```bash
git worktree add "../.worktrees/$(basename $(pwd))/feature-x" -b feature-x
```

### 创建 Worktree（已有分支）
```bash
git worktree add "../.worktrees/$(basename $(pwd))/feature-x" feature-x
```

### 删除 Worktree
```bash
git worktree remove "../.worktrees/{project}/{branch-name}"
```

### 强制删除（有未提交更改时）
```bash
git worktree remove --force "../.worktrees/{project}/{branch-name}"
```

### 清理无效 Worktree 记录
```bash
git worktree prune
```

## 场景示例

### 场景 1：并行开发两个功能

```
用户：我需要同时开发登录功能和支付功能

浮浮酱：
1. 创建 worktree: feature-login
2. 创建 worktree: feature-payment
3. 在 feature-login 中开发登录功能
4. 在 feature-payment 中开发支付功能
5. 分别完成后合并到 main
```

### 场景 2：隔离实验

```
用户：我想试试用新框架重写这个模块，但不想影响现有代码

浮浮酱：
1. 创建 worktree: experiment/new-framework
2. 在实验分支中进行重写
3. 如果成功 → 合并到 main
4. 如果失败 → 直接删除 worktree，不影响主代码
```

### 场景 3：紧急热修复

```
用户：正在开发新功能，但线上出了 bug 需要紧急修复

浮浮酱：
1. 保持当前 feature 分支工作不变
2. 创建 worktree: hotfix/critical-bug（基于 main）
3. 在 hotfix 中快速修复
4. 合并到 main 并部署
5. 回到 feature 分支继续开发
```

## 注意事项

1. **不要在多个 Worktree 中检出同一个分支**
   - Git 不允许同一分支在多个 worktree 中同时存在

2. **定期同步主分支更新**
   - 避免长期分叉导致合并困难

3. **及时清理不用的 Worktree**
   - 避免磁盘空间浪费
   - 使用 `git worktree prune` 清理无效记录

4. **Worktree 目录命名规范**
   - 路径：`../.worktrees/{项目名}/{分支名}`
   - 放在项目父目录的 `.worktrees` 下，保持主目录整洁

## 工具纪律

遵循 IDEA-006：No Evidence, No Output

| 操作 | 必须验证 |
|------|---------|
| 创建 worktree | `git worktree list` 确认 |
| 切换目录 | `pwd` 确认当前位置 |
| 提交代码 | `git status` + `git log` 确认 |
| 删除 worktree | `git worktree list` 确认已删除 |

## 触发方式

```
用户：/autodev-worktree 创建一个实验分支
用户：帮我创建一个 worktree 用于并行开发
用户：我想在隔离环境中测试新方案
```

---

> ฅ'ω'ฅ 浮浮酱会帮主人管理多个并行开发环境喵～每个功能都有自己的空间，互不干扰！
