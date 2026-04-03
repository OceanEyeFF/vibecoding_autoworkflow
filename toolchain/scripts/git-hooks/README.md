# Git Hooks

本目录提供 repo-local 的 git hooks 入口，用于在本地阻断明显违规的操作。

## 安装

```bash
git config core.hooksPath toolchain/scripts/git-hooks
chmod +x toolchain/scripts/git-hooks/pre-push
```

## 当前 Hook

- `pre-push`：禁止直接 push 到 `main`，要求走 PR。
