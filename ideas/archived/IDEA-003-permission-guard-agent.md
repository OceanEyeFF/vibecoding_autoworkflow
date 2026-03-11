# Claude Code Agent 设计基线：鉴权 Agent 设计

> ⚠️ **归档原因**：本设计基于"运行时 Agent 调用"假设，与 ClaudeCode 实际工作流程不兼容
>
> **ClaudeCode 限制**：
> - Agent 是独立会话，无法嵌套调用
> - 无运行时 Orchestrator 解析 JSON 命令
> - 无强制 Schema 验证机制
>
> **可行替代方案**：参见 [归档索引](./README.md)
>
> **归档时间**：2026-01-04

---

> 编号：IDEA-003
> 优先级：P1
> 关联问题：P03（缺少鉴权 Agent）

---

## 一、问题回顾

当前所有 Agent 都是 `permissionMode: default`，没有：
- 敏感操作分级
- 无人值守模式的鉴权逻辑
- 操作风险评估

导致：
- 在 CI 环境无法安全运行
- 要么全部放行（危险），要么全部阻塞（无法自动化）

---

## 二、设计目标

1. 定义操作风险等级（L1-L4）
2. 设计 `permission-guard` Agent 进行鉴权
3. 支持三种运行模式：交互式 / 半自动 / 无人值守

---

## 三、设计方案

### 3.1 操作风险等级定义

| 等级 | 描述 | 示例 | 默认行为 |
|------|------|------|---------|
| **L1** | 只读操作 | Read, Grep, Glob | 自动放行 |
| **L2** | 可逆写操作 | 创建文件、git add | 交互确认 / 自动放行 |
| **L3** | 不可逆写操作 | 删除文件、git commit | 必须确认 |
| **L4** | 远程操作 | git push、API 调用、网络请求 | 必须双重确认 |

### 3.2 permission-guard Agent 设计

```yaml
---
name: permission-guard
description: >
  鉴权 Agent，负责评估操作风险并决定是否放行
tools: Read
model: haiku  # 轻量模型，快速决策
---

## 职责

1. 接收其他 Agent 的操作请求
2. 评估风险等级
3. 根据运行模式决定是否放行

## 输入格式

​```json
{
  "action": "PERMISSION_REQUEST",
  "operation": "DELETE_FILE",
  "target": "/path/to/file",
  "agent": "feature-shipper",
  "context": "清理临时文件"
}
​```

## 输出格式

​```json
{
  "decision": "APPROVE" | "DENY" | "REQUIRE_CONFIRM",
  "risk_level": "L1" | "L2" | "L3" | "L4",
  "reason": "评估理由",
  "conditions": ["如果有条件放行，列出条件"]
}
​```
```

### 3.3 运行模式

| 模式 | L1 | L2 | L3 | L4 | 适用场景 |
|------|----|----|----|----|---------|
| **交互式** | 自动 | 确认 | 确认 | 双重确认 | 本地开发 |
| **半自动** | 自动 | 自动 | 确认 | 确认 | 本地 CI |
| **无人值守** | 自动 | 自动 | 自动* | 拒绝 | 远程 CI |

*无人值守模式下 L3 操作需要预先配置白名单

### 3.4 配置文件

```json
// .autoworkflow/permission-policy.json
{
  "mode": "interactive" | "semi-auto" | "unattended",
  "whitelist": {
    "L3": [
      "DELETE_FILE:.autoworkflow/tmp/*",
      "GIT_COMMIT:*"
    ],
    "L4": []
  },
  "blacklist": {
    "L4": [
      "GIT_PUSH:main",
      "GIT_PUSH:master"
    ]
  },
  "timeout_seconds": 60,
  "default_on_timeout": "DENY"
}
```

### 3.5 集成到现有 Agent

在每个 Agent 的敏感操作前，添加鉴权调用：

```markdown
## 敏感操作前的鉴权（强制）

执行以下操作前，必须先请求鉴权：

| 操作类型 | 风险等级 | 触发条件 |
|---------|---------|---------|
| 删除文件 | L3 | 任何 rm/del 命令 |
| 修改系统文件 | L3 | 路径含 /etc, /system, C:\Windows |
| Git commit | L3 | 任何 git commit |
| Git push | L4 | 任何 git push |
| API 调用 | L4 | 任何网络请求 |

请求格式：
​```json
{
  "action": "PERMISSION_REQUEST",
  "operation": "...",
  "target": "...",
  "agent": "feature-shipper",
  "context": "..."
}
​```

等待 permission-guard 返回 APPROVE 后才能执行。
```

---

## 四、实现路径

### 阶段 1：定义风险等级
- 在 TOOLCHAIN.md 中添加风险等级表
- 在每个 Agent 中标注敏感操作

### 阶段 2：创建 permission-guard Agent
- 创建 `toolchain/agents/permission-guard.md`
- 实现风险评估逻辑

### 阶段 3：集成到工作流
- 在 feature-shipper 中添加鉴权调用
- 创建 `permission-policy.json` 配置

### 阶段 4：CI 集成
- 添加无人值守模式支持
- 添加白名单/黑名单配置

---

## 五、验收标准

- [ ] 有明确的操作风险等级定义（L1-L4）
- [ ] permission-guard Agent 可以评估操作风险
- [ ] 支持三种运行模式
- [ ] 在 CI 环境中可以无人值守运行（有安全保障）

---

## 六、相关文件

- 待创建：`toolchain/agents/permission-guard.md`
- 待创建：`toolchain/schemas/permission-request.json`
- 待创建：`.autoworkflow/permission-policy.json`（模板）

---

> 核心思想：安全第一，默认拒绝，显式放行
