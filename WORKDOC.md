# Autoworkflow + Agents SDK 对齐（临时工作文档）

更新时间：2025-12-26  
作者：浮浮酱  
当前验收节点：A（功能等价链路 + 冷启动安全）✅

---

## 1. 背景与目标

本仓库目标是把“对话驱动（本地）”与“CI 事件驱动（流水线）”统一到一套低门槛、可闭环、可审计的自动化流程上，并逐步向官方推荐形态靠拢：
- `openai-agents/agents` + `MCPServerStdio`（Codex MCP stdio）
- 多 Agent handoff 编排
- `approval-policy` / `sandbox` 可配置（CI 与本地默认策略不同）

---

## 2. 当前已落地产物（可用）

**核心工具链（repo-local）**
- `codex-skills/feature-shipper/scripts/autoworkflow.py`：`init / set-gate / auto-gate / gate / plan(gen|review|status) / plan ci-template / doctor`
- `agents_runner.py`：串行编排 `plan review -> gate`，并写入 trace：`<repo>/.autoworkflow/trace/*.jsonl`

**官方方向（SDK 化）**
- `agents_sdk_runner.py`：提供 3 种模式
  - `--mode local`：用子进程复用 `autoworkflow`（不依赖 Agents SDK）
  - `--mode mcp-smoke`：仅验证 `MCPServerStdio` 能启动/关闭（不需要 `OPENAI_API_KEY`）
  - `--mode sdk`：走 Agents SDK + MCP 的多 Agent handoff（需要 `OPENAI_API_KEY`；尚未作为验收通过项）
- 依赖提示文件：`requirements-agents-sdk.txt`

**CI 模板**
- `.github/workflows/aw-plan-gate.yml`：已与 `autoworkflow.py plan ci-template` 输出对齐（含 schedule 开关与 optional SDK step）

**安全测试（不污染现有项目目录）**
- `codex-skills/feature-shipper/scripts/safe-smoke.ps1`
- `codex-skills/feature-shipper/scripts/safe-smoke.sh`

---

## 3. 已验证的验收（证据）

### 3.1 真实 Codex CLI 运行环境（通过）

已在真实 `codex exec --full-auto` 环境中按顺序跑通：
1) `python -m py_compile ...`
2) `python .autoworkflow/tools/autoworkflow.py --root . plan review`
3) `python .autoworkflow/tools/autoworkflow.py --root . gate --allow-unreviewed`
4) `python agents_runner.py --root . --allow-unreviewed`

要点：
- 修复了参数顺序坑：`--root` 必须放在子命令前（`autoworkflow.py --root . plan review`）
- 产出 trace：`<repo>/.autoworkflow/trace/*.jsonl`

### 3.2 冷启动安全验收（通过，推荐给现有项目）

该测试会把“当前项目”复制到临时目录后再执行（不改动你的原工作目录），并从 0 初始化跑通闭环：
- `init --force`
- `set-gate --create`（默认用 `py_compile` 做一个“真实 test 命令”）
- `plan gen / plan review / gate`
- `agents_runner.py` 写 trace

Windows：
```powershell
powershell -ExecutionPolicy Bypass -File "./codex-skills/feature-shipper/scripts/safe-smoke.ps1" -Root "."
```

保留临时目录（便于复盘临时 trace/产物）：
```powershell
powershell -ExecutionPolicy Bypass -File "./codex-skills/feature-shipper/scripts/safe-smoke.ps1" -Root "." -KeepTemp
```

可选：在临时目录再跑一遍真实 Codex CLI（会联网/有费用）：
```powershell
powershell -ExecutionPolicy Bypass -File "./codex-skills/feature-shipper/scripts/safe-smoke.ps1" -Root "." -UseCodex
```

---

## 4. 功能等价口径（v2：基于 Claude Code 官方 Subagents/Skills）

口径（✅=已作为验收通过项；⚠️=已实现但未完成“实跑验收”；❌=未实现）：

1) Claude Code Subagents（官方形态）✅：`.claude/agents/*.md` 使用 YAML frontmatter（name/description/tools/permissionMode/skills 等），中枢 `feature-shipper` + 专用 subagents 可被显式/自动调用  
2) Claude Code Skills（官方形态）✅：`.claude/skills/*/SKILL.md`（含 `name`/`description`/可选 `allowed-tools`），且 subagent 通过 `skills:` 显式声明以加载（子代理默认不继承 skills）  
3) Repo-local Workflow/Gate 工具链 ✅：`.autoworkflow/tools/`（`autoworkflow.py` + `aw.ps1|aw.sh` + `gate.ps1|gate.sh`），目标平台 Windows pwsh + WSL/Linux  
4) 单一“测试全绿”门禁 ✅：`.autoworkflow/gate.env` 作为 Build/Test/Lint/Format 源，`gate` 只读配置并输出结果（失败附 highlights/tail 追加到 `state.md`）  
5) Plan → Review → Gate 闭环 ✅：`autoworkflow.py plan gen/review` + `gate` 默认要求 review=approve（可显式 `--allow-unreviewed` 覆盖）  
6) 可审计 Trace ✅：`<repo>/.autoworkflow/trace/*.jsonl` 记录关键步骤与输出，便于 CI/复盘  
7) CI 模板/入口 ✅：`autoworkflow.py plan ci-template` 生成 GitHub/GitLab 流水线（plan review → gate → trace artifact）

**当前验收覆盖率（按 ✅ 计）：7/7 = 100%**

---

## 5. 下一阶段（扩展功能，非 v2 最小口径）

目标：在不破坏 v2 最小口径的前提下，补齐“全自动交付”体验（建分支是基础；PR/CI 改造是进阶）：
- B1（Git 基础闭环）：自动建分支（必要）与可选本地 commit（`autoworkflow git branch start` / `autoworkflow git commit`）；PR 创建（gh/glab）作为进阶（需本地已登录）  
- B2（Codex SDK/MCP 端到端）：`agents_sdk_runner.py --mode sdk` 实跑验收（handoff + MCP 工具真实调用 + 产物落盘）  
- B3（全自动 CI 可选 job）：把 `codex exec --full-auto` 固化为 CI 可选 job（默认关闭，通过 `workflow_dispatch` 参数/环境变量启用）  
- B4（权限策略落盘）：把 Claude Code `permissionMode`/skills `allowed-tools` 与 Codex `approval-policy`/`sandbox` 的安全边界写成可审计 policy（并提供最小模板）

---

## 6. 变更记录（本轮）

本轮新增/修改文件（便于 code review）：
- 新增：`WORKDOC.md`
- 新增：`requirements-agents-sdk.txt`
- 新增：`codex-skills/feature-shipper/scripts/safe-smoke.ps1`
- 新增：`codex-skills/feature-shipper/scripts/safe-smoke.sh`
- 修改：`.github/workflows/aw-plan-gate.yml`（修正 `--root` 参数顺序、对齐生成器、补 schedule/optional step）
- 修改：`codex-skills/feature-shipper/scripts/autoworkflow.py`（CI 模板生成内容对齐并修正命令顺序）
- 修改：`agents_runner.py` / `agents_sdk_runner.py` / `agents_workflow.py`（trace 位置指向目标 repo；Windows 文件名安全）
- 修改：`.gitignore`（忽略 `.venv*`）

