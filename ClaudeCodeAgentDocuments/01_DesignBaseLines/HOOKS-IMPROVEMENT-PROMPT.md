# Hooks 改进 Prompt（基于"小需求更稳"设计）

> 本文档用于指导 Hooks 系统的设计与实现，实现门禁、验证和质量把控
> 基于：`AUTODEV_小需求更稳流程设计.md` + `AUTODEV_资料萃取_用于Agent重写与工作流实现.md`
> 生成时间：2026-01-12
> 维护者：浮浮酱

---

## 0. Hooks 体系的核心理念

### 设计目标
- ✅ **把公共硬规则下沉到 Hooks**：避免在每个 Agent 重复堆字
- ✅ **用 Hooks 实现门禁（Gate）**：G0-G4 的检查逻辑自动化
- ✅ **用 Hooks 做证据验证**：自动检查产物完整性与格式合规性
- ✅ **用 Hooks 做上下文注入**：统一注入项目信息/约束/规则

### 核心原则
- ✅ **最小落地优先**：2 个脚本就能显著增稳（pre-agent/inject-context + post-agent/validate-output）
- ✅ **失败快速**：检查不通过立即阻断，不进入下一阶段
- ✅ **可观测性**：所有 Hook 执行必须留日志（时间戳/输入/输出/结果）

---

## 1. Hooks 类型与标准接口

### 1.1 钩子类型定义

| 钩子类型 | 用途 | 触发时机 | 典型用例 |
|---------|------|---------|---------|
| `PreAgentInvoke` | 上下文注入、权限检查 | Agent 调用前 | 注入项目上下文、环境能力、规则约束 |
| `PostAgentInvoke` | 结果验证、日志记录 | Agent 调用后 | 产物完整性检查、格式验证、指标更新 |
| `PreToolUse` | 工具参数校验 | 工具调用前 | 危险命令检查、参数合规性验证 |
| `PostToolUse` | 结果记录/缓存 | 工具调用后 | 变更追踪、结果缓存、日志记录 |
| `OnError` | 错误报告、恢复建议 | 错误发生时 | 错误分类、恢复路径建议、人工介入触发 |
| `OnSessionStart` | 初始化 | 会话开始 | 环境检测、项目信息加载、版本检查 |
| `OnSessionEnd` | 收尾 | 会话结束 | 交付物归档、日志汇总、状态持久化 |

### 1.2 Hook 标准接口（建议）

```bash
#!/bin/bash
# Hook 标准接口
# 输入：通过环境变量或标准输入接收上下文
# 输出：JSON 格式（包含 status/message/data）
# 退出码：0=通过，非0=阻断

# 标准输出格式
{
  "status": "pass|fail|warn",
  "message": "检查结果描述",
  "data": {
    // 额外数据（可选）
  }
}
```

---

## 2. 最小落地方案（两个关键 Hook）

### 2.1 Pre-Agent Hook: `inject-context`

**职责**：统一注入项目上下文、环境能力、规则约束

**输入**：
- Agent 名称
- Agent 版本
- 工作流当前阶段

**输出**：注入到 Agent 上下文的内容
```markdown
## 项目上下文
- 项目名称：[从 package.json/Cargo.toml 读取]
- 项目类型：[语言/框架]
- 环境能力：[编译环境/测试环境/性能测试环境]

## 全局硬规则
- 证据优先：能验证的必须验证，不能验证必须明确风险
- 禁止过度承诺：无证据不得宣称"编译成功/测试通过/性能达标"
- 结构化输出：产物清单 + 验证状态 + 风险 + 下一步

## 固定产物命名
- requirement-contract.md
- review-findings.md
- constraint-compliance.md
- verification-report.md
- risk-matrix.md
- delivery-summary.md

## 当前阶段约束
[根据工作流阶段注入特定约束]
```

**实现要点**：
- 检测项目类型（通过文件特征：package.json/Cargo.toml/pom.xml 等）
- 检测环境能力（编译器/测试框架/性能工具是否可用）
- 根据 Agent 名称注入角色特定约束

---

### 2.2 Post-Agent Hook: `validate-output`

**职责**：验证 Agent 输出的完整性与合规性

**检查项**：
1. **产物完整性检查**
   - 是否生成了约定的产物文件
   - 产物文件是否为空
   - 产物文件是否包含必须字段

2. **禁止项检查**
   - 是否包含占位符（TODO/FIXME/placeholder）
   - 是否包含危险命令（rm -rf/format/DROP TABLE）
   - 是否包含未验证的"通过"宣称

3. **格式检查**
   - Markdown 文件是否包含必须章节
   - JSON 文件是否格式正确
   - 代码文件是否符合基本语法

**输出**：
```json
{
  "status": "pass|fail|warn",
  "message": "验证结果摘要",
  "violations": [
    {
      "type": "missing_artifact|placeholder|dangerous_command|invalid_format",
      "severity": "P0|P1|P2",
      "location": "文件路径:行号",
      "description": "问题描述"
    }
  ]
}
```

**阻断规则**：
- P0 违规：立即阻断，不进入下一阶段
- P1 违规：警告，但允许继续（记录日志）
- P2 违规：建议改进，不阻断

---

## 3. Gate（G0-G4）的 Hook 实现

### 3.1 G0: 入口规模 Gate（Intake-Gatekeeper 后）

**检查项**：
- [ ] SizeScore 评分是否完整（包含命中项列表）
- [ ] 结论是否明确（允许进入/必须拆分/建议拒绝）
- [ ] 若需要拆分，是否给出拆分建议（≤5 个子任务）
- [ ] 每个子任务是否包含验收/风险/验证方式

**阻断条件**：
- SizeScore >= 4 但未给出拆分建议
- 结论模糊（未明确说明下一步）

---

### 3.2 G1: 需求段 Gate（Spec-Gatekeeper 后）

**检查项**：
- [ ] `requirement-contract.md` 是否存在
- [ ] 是否包含 `[MUST-FOLLOW]` 章节且非空
- [ ] 是否包含 `[MUST-VERIFY]` 章节且非空
- [ ] 每条 MUST-VERIFY 是否包含：验证方法 + 容差/阈值 + 测试场景
- [ ] 是否包含环境与平台矩阵
- [ ] 是否包含验收标准（可判定、可复现）
- [ ] 关键术语是否澄清（无"待确认"/"不确定"等模糊表述）

**阻断条件**：
- 任何必须章节缺失
- MUST-VERIFY 缺少验证方法
- 验收标准不可判定（含"尽量"/"基本"/"差不多"等模糊词）

---

### 3.3 G3: 实现段 Gate（Verifier 后）

**检查项**：
- [ ] `constraint-compliance.md` 是否存在
- [ ] `verification-report.md` 是否存在
- [ ] `risk-matrix.md` 是否存在
- [ ] 约束符合度是否逐项对照 MUST-FOLLOW / MUST-VERIFY
- [ ] 验证报告是否包含：编译/测试/数值/性能（按需）
- [ ] 每项验证是否明确标记：通过/失败/无法验证 + 原因
- [ ] 未验证项是否标注风险等级
- [ ] 是否存在 P0 不通过项

**阻断条件**：
- 任何证据三件套缺失
- 存在 P0 不通过项但未给出修复路径
- 存在"无法验证"但未标注风险等级

---

### 3.4 G4: 交付段 Gate（Finalizer 后）

**检查项**：
- [ ] `delivery-summary.md` 是否存在
- [ ] 是否包含交付物清单（文件/入口/使用方式）
- [ ] 是否包含验证摘要与证据索引
- [ ] 是否包含未满足项与风险（按 P0/P1）
- [ ] 是否包含回退/降级方案
- [ ] 是否包含下一步建议（若有未验证项）

**阻断条件**：
- 交付物清单缺失或不完整
- 存在 P0 风险但未给出回退方案
- 存在未验证项但未给出下一步建议

---

## 4. 三层钩子体系（渐进增强方案）

### 4.1 Layer 0: 最小门禁（优先实现）
- `pre-agent/inject-context`：注入项目上下文与全局规则
- `post-agent/validate-output`：产物完整性与格式检查
- `post-agent/gate-G1`：需求契约门禁
- `post-agent/gate-G3`：证据验证门禁

### 4.2 Layer 1: 证据增强
- `post-agent/evidence-validator`：深度验证证据三件套
- `post-tool/change-tracker`：追踪文件变更与版本
- `on-error/recovery-suggester`：错误分类与恢复路径建议

### 4.3 Layer 2: 可观测性增强
- `on-session-start/environment-detector`：环境能力自动检测
- `on-session-end/metrics-collector`：指标收集与报告
- `post-agent/log-aggregator`：日志汇总与归档

---

## 5. Hook 配置规范（config.json）

### 5.1 目录结构（建议）
```
.claude/
  hooks/
    config.json          # 全局配置
    pre-agent/
      inject-context.sh
    post-agent/
      validate-output.sh
      gate-G1.sh
      gate-G3.sh
      gate-G4.sh
    post-tool/
      change-tracker.sh
    on-error/
      recovery-suggester.sh
    on-session-start/
      environment-detector.sh
    on-session-end/
      metrics-collector.sh
```

### 5.2 配置文件结构
```json
{
  "version": "1.0",
  "hooks": {
    "pre-agent": [
      {
        "name": "inject-context",
        "script": "pre-agent/inject-context.sh",
        "enabled": true,
        "timeout": 5000,
        "description": "注入项目上下文与全局规则"
      }
    ],
    "post-agent": [
      {
        "name": "validate-output",
        "script": "post-agent/validate-output.sh",
        "enabled": true,
        "timeout": 10000,
        "blocking": true,
        "description": "产物完整性与格式检查"
      },
      {
        "name": "gate-G1",
        "script": "post-agent/gate-G1.sh",
        "enabled": true,
        "timeout": 5000,
        "blocking": true,
        "condition": "agent.name == 'Spec-Gatekeeper'",
        "description": "需求契约门禁"
      },
      {
        "name": "gate-G3",
        "script": "post-agent/gate-G3.sh",
        "enabled": true,
        "timeout": 5000,
        "blocking": true,
        "condition": "agent.name == 'Verifier'",
        "description": "证据验证门禁"
      }
    ],
    "on-error": [
      {
        "name": "recovery-suggester",
        "script": "on-error/recovery-suggester.sh",
        "enabled": true,
        "timeout": 3000,
        "description": "错误分类与恢复路径建议"
      }
    ]
  }
}
```

---

## 6. Hook 实现模板

### 6.1 Pre-Agent Hook 模板
```bash
#!/bin/bash
# Pre-Agent Hook: inject-context
# 输入：$AGENT_NAME, $AGENT_VERSION, $WORKFLOW_STAGE
# 输出：JSON 格式的注入内容

set -euo pipefail

# 检测项目类型
detect_project_type() {
  if [ -f "package.json" ]; then
    echo "nodejs"
  elif [ -f "Cargo.toml" ]; then
    echo "rust"
  elif [ -f "pom.xml" ]; then
    echo "java"
  else
    echo "unknown"
  fi
}

# 检测环境能力
detect_environment() {
  local capabilities=()

  if command -v node &> /dev/null; then
    capabilities+=("nodejs")
  fi

  if command -v cargo &> /dev/null; then
    capabilities+=("rust")
  fi

  if command -v mvn &> /dev/null; then
    capabilities+=("maven")
  fi

  echo "${capabilities[@]}"
}

# 生成注入内容
generate_context() {
  local project_type=$(detect_project_type)
  local environment=$(detect_environment)

  cat <<EOF
{
  "status": "pass",
  "message": "上下文注入成功",
  "data": {
    "project_type": "$project_type",
    "environment": "$environment",
    "global_rules": [
      "证据优先：能验证的必须验证",
      "禁止过度承诺：无证据不得宣称通过",
      "结构化输出：产物清单+验证状态+风险"
    ],
    "artifact_names": {
      "requirement_contract": "requirement-contract.md",
      "review_findings": "review-findings.md",
      "constraint_compliance": "constraint-compliance.md",
      "verification_report": "verification-report.md",
      "risk_matrix": "risk-matrix.md",
      "delivery_summary": "delivery-summary.md"
    }
  }
}
EOF
}

# 执行
generate_context
exit 0
```

### 6.2 Post-Agent Hook 模板
```bash
#!/bin/bash
# Post-Agent Hook: validate-output
# 输入：$AGENT_NAME, $OUTPUT_DIR
# 输出：JSON 格式的验证结果

set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-.}"
VIOLATIONS=()

# 检查产物完整性
check_artifacts() {
  local required_artifacts=()

  case "$AGENT_NAME" in
    "Spec-Owner")
      required_artifacts=("requirement-contract.md")
      ;;
    "Reviewer")
      required_artifacts=("review-findings.md")
      ;;
    "Verifier")
      required_artifacts=("verification-report.md" "constraint-compliance.md" "risk-matrix.md")
      ;;
    "Finalizer")
      required_artifacts=("delivery-summary.md")
      ;;
  esac

  for artifact in "${required_artifacts[@]}"; do
    if [ ! -f "$OUTPUT_DIR/$artifact" ]; then
      VIOLATIONS+=("{\"type\":\"missing_artifact\",\"severity\":\"P0\",\"location\":\"$artifact\",\"description\":\"必须产物缺失\"}")
    elif [ ! -s "$OUTPUT_DIR/$artifact" ]; then
      VIOLATIONS+=("{\"type\":\"empty_artifact\",\"severity\":\"P0\",\"location\":\"$artifact\",\"description\":\"产物文件为空\"}")
    fi
  done
}

# 检查占位符
check_placeholders() {
  local files=$(find "$OUTPUT_DIR" -type f -name "*.md" 2>/dev/null || true)

  for file in $files; do
    if grep -nE "TODO|FIXME|placeholder|待确认|待实现" "$file" > /dev/null 2>&1; then
      local line=$(grep -nE "TODO|FIXME|placeholder|待确认|待实现" "$file" | head -1 | cut -d: -f1)
      VIOLATIONS+=("{\"type\":\"placeholder\",\"severity\":\"P1\",\"location\":\"$file:$line\",\"description\":\"包含占位符\"}")
    fi
  done
}

# 生成输出
generate_output() {
  local status="pass"
  local message="验证通过"

  if [ ${#VIOLATIONS[@]} -gt 0 ]; then
    # 检查是否有 P0 违规
    if echo "${VIOLATIONS[@]}" | grep -q "P0"; then
      status="fail"
      message="存在 P0 违规，阻断进入下一阶段"
    else
      status="warn"
      message="存在 P1/P2 违规，建议改进"
    fi
  fi

  cat <<EOF
{
  "status": "$status",
  "message": "$message",
  "violations": [
    $(IFS=,; echo "${VIOLATIONS[*]}")
  ]
}
EOF
}

# 执行
check_artifacts
check_placeholders
generate_output

# 退出码
if echo "${VIOLATIONS[@]}" | grep -q "P0"; then
  exit 1
else
  exit 0
fi
```

---

## 7. Hook 日志规范

### 7.1 日志格式
```json
{
  "timestamp": "2026-01-12T10:30:00Z",
  "hook_type": "post-agent",
  "hook_name": "validate-output",
  "agent_name": "Spec-Owner",
  "status": "pass|fail|warn",
  "duration_ms": 1234,
  "input": {
    // 输入参数
  },
  "output": {
    // 输出结果
  }
}
```

### 7.2 日志存储
- 位置：`.claude/hooks/logs/YYYY-MM-DD.log`
- 格式：每行一个 JSON 对象（便于解析）
- 轮转：每天一个文件，保留最近 30 天

---

## 8. 成功度量

### 8.1 门禁效果
- P0 问题阻断率：100%（所有 P0 违规必须阻断）
- P0 问题前移率：≥80%（在 G1/G3 发现，而不是拖到最终诊断）

### 8.2 证据覆盖率
- 小需求任务证据三件套产出率：100%
- 证据格式合规率：≥95%（通过 validate-output 检查）

### 8.3 可观测性
- Hook 执行日志覆盖率：100%（所有 Hook 执行必须留日志）
- Hook 执行超时率：≤1%（超时说明 Hook 设计有问题）

---

## 附录：快速决策卡（10秒版）

| Hook 类型 | 关键职责 | 阻断规则 |
|----------|---------|---------|
| **Pre-Agent** | 注入上下文/规则 | 环境缺失可警告，不阻断 |
| **Post-Agent** | 产物验证/门禁 | P0 违规必须阻断 |
| **Gate-G1** | 需求契约完整性 | MUST-VERIFY 缺验证方法→阻断 |
| **Gate-G3** | 证据三件套完整性 | 任何证据缺失→阻断 |
| **Gate-G4** | 交付物完整性 | 交付清单不完整→阻断 |

---

**版本**：v0.1
**最后更新**：2026-01-12
**下次评审**：2026-04-12
