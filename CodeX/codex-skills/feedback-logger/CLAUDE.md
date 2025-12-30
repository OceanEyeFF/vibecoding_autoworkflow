# Codex Skill：feedback-logger（可选后台日志）

## 能力概述
- 初始化 feedback 监听，监控 `.autoworkflow/*` 变更，写入 `.autoworkflow/logs/feedback.jsonl`
- 手工追加关键信息：假设/结论/TODO/故障摘要
- 包裹命令运行并记录失败高亮与尾部输出

## CLI 入口
`python scripts/feedback.py <subcommand> [--root <repo>]`

子命令（常用）：
- `init`：创建日志目录与工具脚本
- `start` / `stop`：启动/停止后台 watch（ps1/sh 包装：`fb.ps1 start|stop`，`fb.sh start|stop`）
- `log --message "..." --tag hypothesis|note|todo`：手工记录
- `wrap --tag gate -- <command>`：执行命令并记录失败高亮+tail

工具脚本：`.autoworkflow/tools/fb.ps1`、`fb.sh`

## 使用场景
- 改进测试/调试时保留上下文与尝试路径，避免重复踩坑
- 收集 flaky、编译失败的关键输出，便于回溯

## 建议工作流
1) `feedback.py init`（或通过全局路径运行）
2) `fb.ps1 start` / `fb.sh start`（后台监听）
3) 关键命令用 `fb.ps1 wrap --tag gate ...` 捕获失败日志
4) 重要假设/结论用 `fb.ps1 log --tag hypothesis --message "..."` 记录
5) 调试完毕 `fb.ps1 stop`，日志保留在 `.autoworkflow/logs/feedback.jsonl`

## 存储与提交
- 日志文件默认不提交（`.autoworkflow/.gitignore` 已屏蔽）；保持 repo 干净。
- 若需共享，可手动摘录重点片段到 issue / PR 描述。

## 跨平台
- `.ps1` / `.sh` 等价实现；Windows 用 PowerShell，WSL/Ubuntu 用 Bash。
