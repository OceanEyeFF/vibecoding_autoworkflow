# Git Hooks

本目录提供 repo-local 的 git hooks 入口，用于在本地阻断明显违规的操作。

分支治理基线不写死默认分支名。hook 应优先从 `origin/HEAD` 动态解析 protected baseline；当前仓库已验证为 `origin/HEAD -> master`。

## 安装

```bash
git config core.hooksPath toolchain/scripts/git-hooks
chmod +x toolchain/scripts/git-hooks/pre-push
```

## 当前 Hook

- `pre-push`：禁止直接 push 到 protected baseline，要求走 PR。
  - 正常路径：解析 `origin/HEAD`，阻断对应 baseline branch。
  - 保守 fallback：若 `origin/HEAD` 无法解析，阻断 `main` 与 `master`。
