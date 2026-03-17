---
title: "IDEA-006 Layer 3: Hooks 验证机制"
status: archived
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# IDEA-006 Layer 3: Hooks 验证机制

> 实施难度：⭐⭐⭐ 高
> 效果强度：⭐⭐⭐⭐ 高（外部强制验证）
> 适用场景：需要严格约束的场景

---

## 一、核心改进

使用 Claude Code 的 Hooks 机制，在 Agent 输出**之后**进行外部验证。

---

## 二、Hooks 机制说明

Claude Code 支持在特定事件触发时执行外部脚本：

| Hook 类型 | 触发时机 | 用途 |
|----------|---------|------|
| PreToolUse | 工具调用前 | 拦截/修改工具调用 |
| PostToolUse | 工具调用后 | 记录/验证工具结果 |
| Stop | Agent 准备停止时 | 验证最终输出 |

**我们主要使用**：
- `PostToolUse`：记录本轮工具调用
- `Stop`：验证输出是否有足够证据

---

## 三、实现方案

### 3.1 目录结构

```
.claude/
├── settings.json            # Hooks 配置
└── hooks/
    ├── track-tool-calls.py  # 记录工具调用
    ├── validate-evidence.py # 验证证据
    └── tool-call-log.json   # 临时存储本轮调用
```

### 3.2 settings.json 配置

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "command": "python .claude/hooks/track-tool-calls.py",
        "description": "记录每次工具调用"
      }
    ],
    "Stop": [
      {
        "command": "python .claude/hooks/validate-evidence.py",
        "description": "验证输出是否有足够证据"
      }
    ]
  }
}
```

### 3.3 track-tool-calls.py

```python
#!/usr/bin/env python3
"""
PostToolUse Hook: 记录每次工具调用到临时文件
"""

import json
import sys
import os
from datetime import datetime

LOG_FILE = ".claude/hooks/tool-call-log.json"

def main():
    # 从 stdin 读取 Hook 输入
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool", "unknown")
    tool_input = hook_input.get("input", {})
    tool_output = hook_input.get("output", "")

    # 加载或初始化日志
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            log = json.load(f)
    else:
        log = {"session_start": datetime.now().isoformat(), "calls": []}

    # 记录本次调用
    log["calls"].append({
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "input_summary": str(tool_input)[:200],  # 截断
        "output_summary": str(tool_output)[:500]  # 截断
    })

    # 保存
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    # 返回成功，允许继续
    print(json.dumps({"status": "continue"}))

if __name__ == "__main__":
    main()
```

### 3.4 validate-evidence.py

```python
#!/usr/bin/env python3
"""
Stop Hook: 验证 Agent 输出是否有足够证据

验证规则：
1. 如果 Agent 声称读取了文件，检查 tool-call-log 中是否有 Read 调用
2. 如果 Agent 声称搜索了代码，检查是否有 Grep 调用
3. 如果声称很多但调用很少，警告或阻断
"""

import json
import sys
import os
import re

LOG_FILE = ".claude/hooks/tool-call-log.json"

def extract_claims_from_output(output: str) -> list:
    """从 Agent 输出中提取事实陈述"""
    claims = []

    # 尝试解析 JSON 输出
    json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            if "claims" in data:
                claims = [c.get("statement", "") for c in data["claims"]]
            if "evidence_summary" in data:
                return claims, data["evidence_summary"]
        except json.JSONDecodeError:
            pass

    # 启发式提取（如果没有 JSON）
    # 检测文件路径引用
    file_refs = re.findall(r'[`"\']?[\w/\\]+\.(py|js|ts|md|json|yaml)[`"\']?', output)
    if file_refs:
        claims.append(f"引用了文件: {file_refs}")

    return claims, None

def load_tool_calls() -> list:
    """加载本轮工具调用记录"""
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as f:
        log = json.load(f)
        return log.get("calls", [])

def validate(output: str) -> dict:
    """验证输出"""
    claims, evidence_summary = extract_claims_from_output(output)
    tool_calls = load_tool_calls()

    issues = []

    # 检查1：如果有文件引用但没有 Read 调用
    file_mentioned = any("src/" in c or ".py" in c or ".js" in c for c in claims)
    read_called = any(c["tool"] == "Read" for c in tool_calls)

    if file_mentioned and not read_called:
        issues.append("提到了文件但没有 Read 调用")

    # 检查2：如果声称搜索但没有 Grep 调用
    search_mentioned = any("找到" in c or "搜索" in c or "匹配" in c for c in claims)
    grep_called = any(c["tool"] in ["Grep", "Glob"] for c in tool_calls)

    if search_mentioned and not grep_called:
        issues.append("声称搜索但没有 Grep/Glob 调用")

    # 检查3：如果 evidence_summary 与实际不符
    if evidence_summary:
        claimed_calls = evidence_summary.get("tool_calls_this_turn", 0)
        actual_calls = len(tool_calls)

        if claimed_calls != actual_calls:
            issues.append(f"声称调用 {claimed_calls} 次，实际 {actual_calls} 次")

    # 检查4：高置信度声明没有证据
    # (这需要更复杂的解析，暂时跳过)

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "tool_calls_count": len(tool_calls),
        "claims_count": len(claims)
    }

def main():
    # 从 stdin 读取 Agent 输出
    agent_output = sys.stdin.read()

    result = validate(agent_output)

    if result["valid"]:
        # 验证通过，允许输出
        print(json.dumps({
            "status": "continue",
            "validation": "PASS",
            "tool_calls": result["tool_calls_count"]
        }))
    else:
        # 验证失败
        # 选项1：警告但允许（soft block）
        print(json.dumps({
            "status": "continue",  # 或 "block" 进行硬阻断
            "validation": "WARN",
            "issues": result["issues"],
            "message": f"⚠️ 证据验证警告: {', '.join(result['issues'])}"
        }))

        # 选项2：硬阻断（取消下面的注释）
        # print(json.dumps({
        #     "status": "block",
        #     "validation": "FAIL",
        #     "issues": result["issues"],
        #     "message": "❌ 证据不足，输出被阻断"
        # }))
        # sys.exit(2)  # 非零退出码阻断

    # 清理临时日志（为下一轮准备）
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

if __name__ == "__main__":
    main()
```

---

## 四、工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Agent 开始工作                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Agent 调用工具 (Read/Grep/Bash)                          │
│    ↓                                                        │
│    PostToolUse Hook 触发                                    │
│    ↓                                                        │
│    track-tool-calls.py 记录到 tool-call-log.json            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Agent 准备输出结论                                       │
│    ↓                                                        │
│    Stop Hook 触发                                           │
│    ↓                                                        │
│    validate-evidence.py 验证：                              │
│    - 声称 vs 实际调用是否匹配？                              │
│    - evidence_summary 是否准确？                            │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌─────────────┐     ┌─────────────┐
            │ 验证通过     │     │ 验证失败     │
            │ 输出继续     │     │ 警告/阻断   │
            └─────────────┘     └─────────────┘
```

---

## 五、配置选项

### 5.1 软阻断（推荐初期使用）

```python
# validate-evidence.py 中
print(json.dumps({
    "status": "continue",  # 允许继续，但显示警告
    "validation": "WARN",
    "message": "⚠️ 证据验证警告"
}))
```

### 5.2 硬阻断（严格模式）

```python
# validate-evidence.py 中
print(json.dumps({
    "status": "block",     # 阻断输出
    "validation": "FAIL"
}))
sys.exit(2)  # 非零退出码
```

### 5.3 白名单（排除某些 Agent）

```python
# validate-evidence.py 中
WHITELIST_AGENTS = ["requirement-refiner"]  # 需求精炼可能不需要工具调用

agent_name = extract_agent_name(agent_output)
if agent_name in WHITELIST_AGENTS:
    print(json.dumps({"status": "continue", "validation": "SKIP"}))
    sys.exit(0)
```

---

## 六、安装步骤

```bash
# 1. 创建目录
mkdir -p .claude/hooks

# 2. 复制脚本
cp track-tool-calls.py .claude/hooks/
cp validate-evidence.py .claude/hooks/

# 3. 添加执行权限 (Linux/Mac)
chmod +x .claude/hooks/*.py

# 4. 配置 settings.json
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {"command": "python .claude/hooks/track-tool-calls.py"}
    ],
    "Stop": [
      {"command": "python .claude/hooks/validate-evidence.py"}
    ]
  }
}
EOF

# 5. 测试
echo '{"tool": "Read", "input": {"path": "test.py"}}' | python .claude/hooks/track-tool-calls.py
```

---

## 七、效果评估

| 指标 | 预期效果 |
|------|---------|
| 强制力 | 高（外部验证，Agent 无法绕过） |
| 幻觉检测率 | 高（对比声称 vs 实际调用） |
| 误报率 | 中（需要调优阈值） |
| 实施成本 | 高（需要维护脚本） |

---

## 八、局限性

⚠️ **Hooks 的限制**：
- Claude Code 的 Hooks 支持可能因版本而异
- 复杂验证逻辑难以用 shell 脚本实现（推荐 Python）
- 无法在工具调用**之前**验证意图

⚠️ **验证逻辑的限制**：
- 启发式提取 claims 可能不准确
- 无法检测"正确调用了工具但错误解读结果"

---

## 九、进阶方案：Agent SDK

如果需要**最强的约束**，考虑使用 Claude Agent SDK：

```python
# 使用 Agent SDK 的 Structured Outputs
from anthropic import Anthropic

client = Anthropic()

# 强制输出必须包含 evidence 字段
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "agent_output",
            "strict": True,
            "schema": {
                "type": "object",
                "required": ["claims", "evidence"],
                "properties": {
                    "claims": {...},
                    "evidence": {
                        "type": "array",
                        "minItems": 1  # 强制至少有一个证据！
                    }
                }
            }
        }
    }
)
```

这样 **JSON Schema 验证是强制的**，Agent 无法输出不符合格式的响应。

---

> 下一步：创建实施总结和优先级建议
