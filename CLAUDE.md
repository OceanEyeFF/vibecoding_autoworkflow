# CLAUDE.md（本仓库）

本仓库的 Claude Code 资源采用"源资产 / 安装产物"分离 + **命名空间隔离**设计：

- **源资产**：`Claude/agents/aw-kernel/`、`Claude/skills/aw-kernel/`（入库维护）
- **安装产物**：`~/.claude/agents/aw-kernel/`、`~/.claude/skills/aw-kernel/`（全局安装）

## 全局安装（推荐）

将源资产安装到 `~/.claude/` 全局目录，所有项目可用：

**Linux/macOS/WSL:**
```bash
bash Claude/scripts/install-global.sh
```

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1
```

## 卸载

```bash
# Linux/macOS/WSL
bash Claude/scripts/install-global.sh --uninstall --namespace aw-kernel

# Windows
powershell -ExecutionPolicy Bypass -File Claude\scripts\install-global.ps1 -Uninstall -Namespace aw-kernel
```

## 详细文档

- [Claude/ 源资产说明](Claude/README.md)
- [安装脚本详细文档](Claude/scripts/README.md)
