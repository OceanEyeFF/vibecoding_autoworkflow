# Claude Code Agent 设计基线：本地化文档缓存

> 编号：IDEA-005
> 优先级：P0
> 关联问题：P05（核心 Agent 无本地化文档缓存）

---

## 一、问题回顾

当前问题：
- feature-shipper 有 236 行 Prompt
- 每次对话都要加载完整 Prompt
- 长对话后，原始指令会被稀释
- LLM 会"忘记"核心约束

---

## 二、设计目标

1. 核心指令外置到文件系统
2. Prompt 只保留"加载指令"的引用
3. 在需要时可以"刷新"指令记忆
4. 避免上下文污染

---

## 三、设计方案

### 3.1 指令分层架构

```
.autoworkflow/
└── agent-instructions/
    ├── _shared/
    │   ├── tool-discipline.md      # 共享工具纪律
    │   ├── output-format.md        # 共享输出格式
    │   └── safety-rules.md         # 共享安全规则
    │
    ├── feature-shipper/
    │   ├── core.md                 # 核心职责和约束
    │   ├── workflow.md             # 工作流程
    │   └── examples.md             # 示例
    │
    ├── requirement-refiner/
    │   ├── core.md
    │   ├── five-stages.md          # 五阶段流程
    │   └── templates.md            # 输出模板
    │
    └── ...
```

### 3.2 精简后的 Prompt

```yaml
---
name: feature-shipper
description: 交付中枢 Agent
tools: Read, Grep, Glob, Bash
subagents: requirement-refiner, code-debug-expert, code-analyzer
instruction_files:
  - .autoworkflow/agent-instructions/_shared/tool-discipline.md
  - .autoworkflow/agent-instructions/_shared/output-format.md
  - .autoworkflow/agent-instructions/feature-shipper/core.md
  - .autoworkflow/agent-instructions/feature-shipper/workflow.md
---

你是一个"交付中枢 Agent"。

## 启动协议（必须执行）

1. 首先读取你的核心指令文件：
   - `Read(.autoworkflow/agent-instructions/feature-shipper/core.md)`
   - `Read(.autoworkflow/agent-instructions/feature-shipper/workflow.md)`

2. 理解并遵循这些指令。

3. 如果指令文件不存在，输出：
   ```json
   {
     "status": "BLOCKED",
     "reason": "缺少指令文件，请先运行 aw-init"
   }
   ```

## 刷新指令（当你感觉"忘记"约束时）

在长对话中，如果你感觉对核心约束的记忆变得模糊：
1. 主动读取 `core.md` 文件
2. 在输出中声明：`[刷新指令记忆]`
3. 按照刷新后的指令继续工作

## 输出格式

遵循 `.autoworkflow/agent-instructions/_shared/output-format.md` 中的规范。
```

### 3.3 核心指令文件示例

#### `feature-shipper/core.md`

```markdown
# Feature Shipper 核心指令

## 不可违背的约束

1. **先明确验收标准再动手**
   - 缺失时先补齐（最多问 3 个问题）
   - 没有明确 DoD 不开始编码

2. **不擅自引入新依赖**
   - 除非明确得到同意

3. **小步改动**
   - 每次只做小步改动
   - 用测试验证

4. **不自作主张**
   - 遇到不确定的业务规则，停下来问

5. **工具纪律**
   - 先查证后输出
   - 先调用再回答
   - 结论必须有证据

## 职责边界

### 我做什么
- 代码实现
- 测试编写
- Gate 验证
- 交付总结

### 我不做什么
- 需求精炼（调用 requirement-refiner）
- 深度调试（调用 code-debug-expert）
- 架构分析（调用 code-analyzer）
```

### 3.4 指令刷新机制

在 Prompt 中添加：

```markdown
## 指令刷新触发条件

当以下情况发生时，你必须主动刷新指令：

1. **对话超过 10 轮**
   - 每 10 轮强制读取一次 core.md

2. **用户反馈你"忘记"了约束**
   - 立即读取 core.md 并道歉

3. **你发现自己在做"不该做的事"**
   - 停止当前操作
   - 读取 core.md
   - 输出 BOUNDARY_VIOLATION

4. **Gate 连续失败 3 次**
   - 读取 core.md 和 workflow.md
   - 评估是否需要调用 SubAgent

刷新时输出：
​```json
{
  "action": "INSTRUCTION_REFRESH",
  "files_read": ["core.md", "workflow.md"],
  "memory_restored": true
}
​```
```

### 3.5 初始化脚本更新

在 `autoworkflow.py init` 中添加：

```python
def create_agent_instructions():
    """创建 agent-instructions 目录结构"""
    instructions_dir = project_root / ".autoworkflow" / "agent-instructions"

    # 创建共享指令
    shared_dir = instructions_dir / "_shared"
    shared_dir.mkdir(parents=True, exist_ok=True)

    copy_template("tool-discipline.md", shared_dir)
    copy_template("output-format.md", shared_dir)
    copy_template("safety-rules.md", shared_dir)

    # 创建各 Agent 指令目录
    for agent in ["feature-shipper", "requirement-refiner", "code-debug-expert"]:
        agent_dir = instructions_dir / agent
        agent_dir.mkdir(exist_ok=True)
        copy_template(f"{agent}/core.md", agent_dir)
```

---

## 四、预期收益

| 指标 | 改进前 | 改进后 |
|------|-------|-------|
| Prompt 长度 | 236 行 | ~50 行 |
| 指令稀释风险 | 高 | 低（可刷新） |
| 共享逻辑 | 复制粘贴 | 集中管理 |
| 可维护性 | 低 | 高 |

---

## 五、验收标准

- [ ] Prompt 精简到 50 行以内
- [ ] 核心指令外置到 `.autoworkflow/agent-instructions/`
- [ ] 有共享指令机制
- [ ] 有指令刷新机制
- [ ] init 脚本能自动创建指令目录

---

## 六、相关文件

- 待修改：`Claude/agents/feature-shipper.md`
- 待创建：`Claude/agents/assets/templates/agent-instructions/`
- 待修改：`Claude/agents/scripts/claude_autoworkflow.py`

---

> 核心思想：指令外置 + 按需加载 + 主动刷新 = 抗遗忘
