# AUTODEV 实施参考

> **版本**：v1.0
> **最后更新**：2026-01-13
> **维护者**：浮浮酱
> **主文档**：[AUTODEV 小需求更稳](AUTODEV_小需求更稳.md)

---

## 0. 何时读我

**应该读**：
- ✅ 需要落地实施 Hooks 系统时
- ✅ 需要创建产物模板时
- ✅ 需要编写门禁脚本时
- ✅ 需要查阅失败模式清单时

**不应读**：
- ❌ 想了解工作流设计理念（请读主文档）
- ❌ 想了解 Agent 职责定义（请读主文档）

---

## 1. Hooks 系统设计

### 1.1 钩子类型与用途

| 钩子类型 | 触发时机 | 典型用途 |
|---------|---------|---------|
| `PreAgentInvoke` | Agent 调用前 | 上下文注入、权限/能力检查 |
| `PostAgentInvoke` | Agent 调用后 | 结果验证、日志记录、指标更新 |
| `PreToolUse` | 工具使用前 | 参数校验、权限检查 |
| `PostToolUse` | 工具使用后 | 结果记录/缓存、变更追踪 |
| `OnError` | 错误发生时 | 错误报告、恢复建议 |
| `OnSessionStart` | 会话开始时 | 初始化、环境检查 |
| `OnSessionEnd` | 会话结束时 | 清理、归档、统计 |

### 1.2 标准接口（建议）

**输入**（通过环境变量或 stdin）：
```json
{
  "agent_name": "spec-owner",
  "phase": "requirement",
  "context": {
    "project_root": "/path/to/project",
    "task_id": "task-001",
    "user_request": "..."
  }
}
```

**输出**（stdout，JSON 格式）：
```json
{
  "status": "success|warning|error",
  "message": "...",
  "inject_context": {
    "key": "value"
  },
  "block": false
}
```

### 1.3 最小落地方案（2 个脚本）

**推荐：先实现这 2 个 Hook，就能显著提升稳定性**

#### 1.3.1 `pre-agent/inject-context.sh`

**用途**：注入项目上下文、环境能力、规则/约束

**实现示例**：
```bash
#!/bin/bash
# inject-context.sh

# 读取输入
INPUT=$(cat)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name')

# 注入上下文
cat <<EOF
{
  "status": "success",
  "inject_context": {
    "project_type": "node",
    "test_command": "npm test",
    "build_command": "npm run build",
    "constraints": [
      "MUST-FOLLOW: 使用 TypeScript strict 模式",
      "MUST-VERIFY: 测试覆盖率 ≥80%"
    ]
  },
  "block": false
}
EOF
```

#### 1.3.2 `post-agent/validate-output.sh`

**用途**：输出验证（占位符、危险命令、缺失关键报告等）

**实现示例**：
```bash
#!/bin/bash
# validate-output.sh

# 读取输入
INPUT=$(cat)
OUTPUT=$(echo "$INPUT" | jq -r '.agent_output')

# 检查占位符
if echo "$OUTPUT" | grep -q "TODO\|FIXME\|XXX"; then
  echo '{"status": "warning", "message": "输出包含占位符", "block": false}'
  exit 0
fi

# 检查必须产物（例如 Verifier 必须产出证据）
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name')
if [ "$AGENT_NAME" = "verifier" ]; then
  if ! echo "$OUTPUT" | grep -q "verification-report.md"; then
    echo '{"status": "error", "message": "Verifier 未产出 verification-report.md", "block": true}'
    exit 0
  fi
fi

echo '{"status": "success", "message": "验证通过", "block": false}'
```

### 1.4 三层钩子体系（进阶）

当基础 2 个脚本稳定后，可扩展为三层体系：

**需求层 Hooks**：
- `post-spec-owner`：检查需求契约完整性
- `post-spec-gatekeeper`：检查放行决策有效性

**实现层 Hooks**：
- `post-implementer`：检查实现产物存在性
- `post-reviewer`：检查 review-findings 结构
- `post-verifier`：检查最小证据集（三件套）

**诊断层 Hooks**：
- `post-finalizer`：检查交付摘要完整性

---

## 2. 产物模板

### 2.1 需求契约模板（requirement-contract.md）

```markdown
# 需求契约

## 任务描述
[简要描述任务目标与背景]

## MUST-FOLLOW（强制约束）
- [ ] [约束1]：描述 + 理由
- [ ] [约束2]：描述 + 理由

## MUST-VERIFY（必须验证项）
- [ ] [验证项1]
  - 验证方法：[如何验证]
  - 容差/阈值：[通过标准]
  - 测试场景：[在哪些场景下验证]
- [ ] [验证项2]
  - ...

## MUST-MEASURE（性能度量项，可选）
- [ ] [度量项1]
  - 度量方法：[如何度量]
  - 基准值：[对标数据]
  - 环境：[度量环境]

## 环境与平台矩阵
| 平台 | 工具链 | 验证可行性 |
|------|--------|----------|
| macOS | Node 20 | ✅ 可本地验证 |
| Linux | Node 20 | ⚠️ 需 CI 验证 |
| Windows | Node 20 | ❌ 暂无环境 |

## 验收标准
- [ ] [可判定的验收条件1]
- [ ] [可判定的验收条件2]

## 风险与降级策略
| 风险 | 降级方案 | 最低证据替代 |
|------|---------|-------------|
| 无编译环境 | 代码静态审查 | 语法检查 + 类型检查 |
| 无测试设备 | 模拟器验证 | 标记"未在真机验证" |
```

### 2.2 约束符合度报告（constraint-compliance.md）

```markdown
# 约束符合度报告

## MUST-FOLLOW 符合度
| 约束 | 状态 | 证据/说明 |
|------|------|---------|
| 使用 TypeScript strict 模式 | ✅ 满足 | tsconfig.json:5 |
| 不使用 any 类型 | ⚠️ 部分满足 | 2处使用 any（见下方） |

## MUST-VERIFY 符合度
| 验证项 | 状态 | 证据/说明 |
|--------|------|---------|
| 编译通过 | ✅ 满足 | `npm run build` 成功 |
| 测试覆盖率 ≥80% | ✅ 满足 | 覆盖率 85%（见 coverage/） |
| 性能不劣化 | ❌ 不满足 | 响应时间增加 20%（见性能基准） |

## MUST-MEASURE 符合度
| 度量项 | 目标值 | 实际值 | 状态 |
|--------|--------|--------|------|
| 响应时间 | ≤100ms | 120ms | ❌ 未达标 |
| 内存占用 | ≤50MB | 45MB | ✅ 达标 |

## 未满足项详情
### P0：性能不劣化
- 位置：API /search 端点
- 原因：新增的数据验证逻辑增加了开销
- 建议：优化验证逻辑或调整目标值
```

### 2.3 验证报告模板（verification-report.md）

```markdown
# 验证报告

## 编译验证
- **状态**：✅ 通过
- **命令**：`npm run build`
- **环境**：Node 20.10.0, macOS 14.2
- **日志摘要**：
  ```
  > build
  > tsc

  Compiled successfully in 3.2s
  ```

## 测试验证
- **状态**：✅ 通过
- **命令**：`npm test -- --coverage`
- **环境**：Node 20.10.0, macOS 14.2
- **结果**：
  - 通过：25/25 (100%)
  - 覆盖率：85%
- **日志摘要**：
  ```
  PASS  src/api.test.ts
  PASS  src/utils.test.ts

  Test Suites: 2 passed, 2 total
  Tests:       25 passed, 25 total
  Coverage:    85%
  ```

## 数值验证
- **状态**：✅ 通过
- **验证内容**：权重和 = 1.0 ± 0.001
- **计算**：sum([0.3, 0.5, 0.2]) = 1.0
- **脚本**：scripts/validate-weights.py

## 性能验证
- **状态**：❌ 失败
- **基准数据**：见 performance-baseline.md
- **未达标项**：响应时间 120ms > 100ms (目标)

## 平台验证矩阵
| 平台 | 编译 | 测试 | 性能 | 备注 |
|------|------|------|------|------|
| macOS | ✅ | ✅ | ❌ | 性能未达标 |
| Linux | ⚠️ | ⚠️ | - | 仅 CI 验证 |
| Windows | ❌ | ❌ | - | 无环境 |
```

### 2.4 风险矩阵模板（risk-matrix.md）

```markdown
# 风险矩阵

## 已验证项
| 项目 | 平台/环境 | 证据 |
|------|----------|------|
| 编译 | macOS | build.log |
| 测试 | macOS | test-results.json |

## 未验证项
| 项目 | 平台/环境 | 风险等级 | 原因 | 建议验证路径 |
|------|----------|---------|------|-------------|
| 测试 | Windows | P1 | 无环境 | 使用 GitHub Actions Windows Runner |
| 性能 | Linux | P1 | 无环境 | 部署到 staging 验证 |
| 跨浏览器 | Safari | P2 | 无设备 | 使用 BrowserStack |

## 仅推断项
| 项目 | 推断依据 | 风险等级 | 备注 |
|------|---------|---------|------|
| Linux 兼容性 | 使用标准 Node API | P2 | CI 通过但未在真实设备验证 |

## 风险等级说明
- **P0**：严重风险，可能导致核心功能失效
- **P1**：中等风险，可能导致部分场景问题
- **P2**：低风险，影响有限或有降级方案
```

### 2.5 交付摘要模板（delivery-summary.md）

```markdown
# 交付摘要

## 交付物清单
- 代码文件：
  - src/api.ts
  - src/utils.ts
- 配置文件：
  - tsconfig.json
  - package.json
- 文档：
  - README.md
  - API.md

## 验证摘要
| 验证类型 | 状态 | 证据 |
|---------|------|------|
| 编译 | ✅ 通过 | verification-report.md § 编译验证 |
| 测试 | ✅ 通过 | verification-report.md § 测试验证 |
| 性能 | ❌ 未达标 | verification-report.md § 性能验证 |

## 未满足项（P0/P1）
### P0：无
### P1：性能未达标
- 响应时间 120ms > 100ms (目标)
- 建议：优化数据验证逻辑

## 风险与回退
| 风险 | 等级 | 回退方案 |
|------|------|---------|
| 性能劣化 | P1 | 回退到 v1.2.3 |
| Windows 未验证 | P1 | 标记"仅支持 macOS/Linux" |

## 下一步建议
1. 优化性能（优先）
2. 在 CI 中添加 Windows 测试
3. 补充 Safari 兼容性验证
```

---

## 3. Gate 检查清单（用于实现门禁脚本）

### 3.1 G0（入口规模 Gate）检查项

**必须检查**：
- [ ] SizeScore 计算正确（10 项检查）
- [ ] 拆分建议包含：目标/验收/范围/风险
- [ ] 每个子任务可在 0.5～2 小时闭环

### 3.2 G1（需求段 Gate）检查项

**必须检查**：
- [ ] 术语澄清（无歧义或已明确定义）
- [ ] `[MUST-FOLLOW]` 齐全且清晰
- [ ] `[MUST-VERIFY]` 包含：验证方法 + 容差 + 场景
- [ ] 平台/环境矩阵明确
- [ ] 验收标准可判定

**可选检查**：
- [ ] 风险与降级策略合理
- [ ] 约束之间不冲突

### 3.3 G3（实现段 Gate）检查项

**必须检查**：
- [ ] 最小证据集完整（三件套）
- [ ] `constraint-compliance.md` 逐项对照
- [ ] P0 项无遗漏
- [ ] 未验证项标注风险

**可选检查**：
- [ ] 性能基准（若有 MUST-MEASURE）
- [ ] 代码质量（若有 linter/formatter 检查）

### 3.4 G4（交付段 Gate）检查项

**必须检查**：
- [ ] 交付物清单完整
- [ ] 证据索引正确
- [ ] 风险/回退方案明确
- [ ] 下一步建议具体

---

## 4. 失败模式清单

> 详细失败模式分析见：[docs/analysis/autodev-insights.md](docs/analysis/autodev-insights.md)
>
> 本节仅列举"可直接转化为 Gate 检查项"的高频失败模式

### 4.1 需求段失败模式

| 失败模式 | 对应 Gate 检查 | Hook 实现 |
|---------|---------------|----------|
| 术语歧义 | G1: 术语澄清 | post-spec-owner: 检测模糊词汇 |
| 验收不可验证 | G1: MUST-VERIFY 完整性 | post-spec-gatekeeper: 检查验证方法 |
| 约束冲突 | G1: 约束一致性 | post-spec-gatekeeper: 冲突检测 |

### 4.2 实现段失败模式

| 失败模式 | 对应 Gate 检查 | Hook 实现 |
|---------|---------------|----------|
| 无证据宣称通过 | G3: 证据完整性 | post-verifier: 检查三件套 |
| P0 遗漏 | G3: P0 无遗漏 | post-reviewer: P0 标记检查 |
| 环境假设未验证 | G3: 平台矩阵 | post-verifier: 矩阵完整性 |

### 4.3 交付段失败模式

| 失败模式 | 对应 Gate 检查 | Hook 实现 |
|---------|---------------|----------|
| 交付物遗漏 | G4: 清单完整性 | post-finalizer: 文件存在性 |
| 无回退方案 | G4: 回退方案 | post-finalizer: 回退字段检查 |
| 风险未标记 | G4: 风险明确性 | post-finalizer: 风险等级检查 |

---

## 5. v0.1 设计约束（落地建议）

### 5.1 单文件实现

- 集中在 `Claude/skills/aw-kernel/autodev/SKILL.md`
- 避免跨多个文件的复杂依赖
- 便于理解和维护

### 5.2 无外部依赖

- 不依赖脚本/状态文件（除 TodoWrite）
- 不依赖特定的 CI/CD 环境
- 可在任意项目中快速启用

### 5.3 Prompt 长度限制

- ≤ 600 行（避免上下文爆炸）
- 通过"下沉公共规则到 Hooks"来压缩长度
- Agent 只保留"职责边界 + 输入输出 + 放行标准"

### 5.4 失败优雅降级

- 失败时给清晰的人工介入指导
- 不要"假装通过"或"静默失败"
- 提供"如何修复/如何复现/如何回退"的具体建议

### 5.5 状态管理

- 仅用 TodoWrite（可见、可恢复）
- 避免隐式状态（如全局变量、文件锁）
- 状态变更必须可追溯

---

## 6. Agent 元信息规范

建议每个 Agent 都具备统一的元信息（便于迭代与回滚）：

```markdown
---
name: <agent-name>
version: <semver>
last_updated: <YYYY-MM-DD>
changelog: |
  - vX.Y.Z (YYYY-MM-DD): ...
---
```

**示例**：
```markdown
---
name: spec-owner
version: 1.0.0
last_updated: 2026-01-13
changelog: |
  - v1.0.0 (2026-01-13): 初始版本，支持 MUST-FOLLOW/MUST-VERIFY/MUST-MEASURE
---
```

---

## 7. 实施优先级建议

### 阶段 1：最小可行（1 周内）
1. 实现入口规模 Gate（SizeScore 评估）
2. 固化需求契约模板（Spec-Owner 输出）
3. 实现 2 个基础 Hook（inject-context + validate-output）

### 阶段 2：门禁强化（2 周内）
1. 实现 G1 门禁（Spec-Gatekeeper 审查清单）
2. 实现 G3 门禁（Verifier 证据三件套检查）
3. 实现 Level 0 回路（最多 3 次修复）

### 阶段 3：完整体系（1 个月内）
1. 实现 G4 门禁（Finalizer 交付检查）
2. 扩展三层钩子体系
3. 补充性能度量（MUST-MEASURE）

---

## 附录：相关文档

| 文档 | 用途 |
|------|------|
| [AUTODEV 小需求更稳](AUTODEV_小需求更稳.md) | 工作流设计与理念 |
| [分析精华](docs/analysis/autodev-insights.md) | 失败模式详细分析 |
| [CLAUDE.md](CLAUDE.md) | 项目宪法与协作规则 |

---

**版本历史**：
- v1.0 (2026-01-13)：从资料萃取重组为实施参考
