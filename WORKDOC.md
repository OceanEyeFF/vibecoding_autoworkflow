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

## 4. 功能等价口径（7 项）与当前覆盖率

口径（✅=已作为验收通过项；⚠️=已实现但未完成“实跑验收”；❌=未实现）：

1) 编排入口（runner）✅：`agents_runner.py`  
2) 门禁守卫（plan review gate）✅：`autoworkflow.py`（gate 默认要求 plan review=approve，可 `--allow-unreviewed` 跳过）  
3) 可审计 trace ✅：`<repo>/.autoworkflow/trace/*.jsonl`  
4) CI 触发入口 ✅：`.github/workflows/aw-plan-gate.yml` + `plan ci-template`  
5) MCP server 可用且被 runner 使用 ⚠️：`agents_sdk_runner.py --mode mcp-smoke` 已通过；`--mode sdk` 尚未作为验收通过项  
6) 多 agent handoff ⚠️：已在 `--mode sdk` 中实现 handoff 结构，但未完成“端到端可复现验收”  
7) 非交互快速路（`codex exec --full-auto`）⚠️：已验证可跑通；但还未固化为 CI 的标准可选 job/入口规范

**当前验收覆盖率（按 ✅ 计）：4/7 = 57.1%**  
（节点 A 的定义就是把 1-4 做到“可跑 + 可复现 + 可审计”。）

---

## 5. 下一阶段（验收节点 B）建议

目标：把 5-7 变成 ✅（有“实跑证据”），并把官方推荐形态真正落到“可复现工程实践”：
- B1：`agents_sdk_runner.py --mode sdk` 端到端验收（handoff + MCP 工具真实调用 + 产物落盘）
- B2：在 CI 中增加可选 job：`codex exec --full-auto`（默认关闭，可通过 `workflow_dispatch` 参数/环境变量启用）
- B3：把 `approval-policy`/`sandbox` 从“文案/约束”升级为“真实透传并生效”的执行策略

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

