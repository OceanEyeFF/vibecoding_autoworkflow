# CLAUDE.md（本仓库）

本仓库的 Claude Code 资源采用“源资产 / 安装产物”分离：

- 源资产：`Claude/`（agents / skills / commands，入库维护）
- 安装产物：`/.claude/`（Claude Code 实际读取的位置；由脚本生成，默认不入库）

在本仓库使用 Claude Code 前，先执行一次 repo-local 安装：

- macOS/Linux/WSL：`bash Claude/scripts/install-local.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File Claude/scripts/install-local.ps1`

历史文档已归档：`Claude/docs/repo-CLAUDE.md`

