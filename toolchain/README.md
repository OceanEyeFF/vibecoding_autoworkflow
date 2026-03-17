# toolchain/ - 源资产目录

> 本目录存放 aw-kernel 的 Agent、Skill、脚本和模板源文件。
> 最后更新：2026-03-17

## 当前结构

```text
toolchain/
├── agents/aw-kernel/          # 6 个 Agent
├── skills/aw-kernel/          # 2 个 Skill
├── scripts/                   # 安装与辅助脚本
├── docs/aw-kernel/            # 工具链规范与说明
└── assets/templates/          # 模板资源
```

## 当前事实

- 当前主线 Agent：`ship`、`review`、`logs`、`clean`、`clarify`、`knowledge-researcher`
- 当前主线 Skill：`autodev`、`autodev-worktree`
- `autodev/v0.1/` 属于历史实现基线，可回溯，但不代表当前规划方向

## 何时读这里

- 需要修改 Agent / Skill 源文件
- 需要运行安装脚本
- 需要查看 aw-kernel 的规范文档

## 何时不要读这里

- 只是想了解当前项目方向：先读 `docs/overview/`
- 只是想知道当前计划状态：先读 `planning/`
