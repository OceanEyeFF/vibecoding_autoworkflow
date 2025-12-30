# CodeX 资源（源资产）

`CodeX/` 存放的是 Codex/Codex CLI 相关的**源资产**（例如 Codex skills）。

本仓库的工作目录（运行后生成的产物）与源资产分离：

- 源资产：`CodeX/codex-skills/`（入库维护）
- 生成工作目录：`/.autoworkflow/`（由 `init` 生成，默认不入库）

在本仓库中初始化（生成 `/.autoworkflow/`）：

- macOS/Linux/WSL：`bash CodeX/scripts/init-local.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File CodeX/scripts/init-local.ps1`

清理（删除本仓库生成的 `/.autoworkflow/`）：

- macOS/Linux/WSL：`bash CodeX/scripts/uninstall-local.sh`
- Windows PowerShell：`powershell -ExecutionPolicy Bypass -File CodeX/scripts/uninstall-local.ps1`

全局安装（安装到 `$CODEX_HOME/skills`，默认 `~/.codex/skills`）：

- `CodeX/codex-skills/feature-shipper/scripts/install-codex-global.sh`
- `CodeX/codex-skills/feature-shipper/scripts/install-codex-global.ps1`

