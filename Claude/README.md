# Claude 资源（源资产）

`Claude/` 存放的是 Claude Code 相关的**源资产**（agents / skills / commands）。

为了让 Claude Code 在本仓库中识别这些资源，需要先把它们同步到仓库根的 `/.claude/`（该目录属于安装产物，默认不入库）：

- macOS/Linux/WSL：`bash Claude/scripts/install-local.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File Claude/scripts/install-local.ps1`

卸载（清理本仓库生成的 `/.claude/`）：

- macOS/Linux/WSL：`bash Claude/scripts/uninstall-local.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File Claude/scripts/uninstall-local.ps1`

全局安装（安装到 `$CLAUDE_HOME`，默认 `~/.claude`）请使用：

- `CodeX/codex-skills/feature-shipper/scripts/install-claude-global.sh`
- `CodeX/codex-skills/feature-shipper/scripts/install-claude-global.ps1`
