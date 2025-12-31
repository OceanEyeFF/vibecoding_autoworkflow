# IDEA-006 实施方案总结

> 目标：强制 Agent 在输出前必须基于工具调用获取证据
> 核心原则：No Evidence, No Output

---

## 一、三层防守架构

```
┌─────────────────────────────────────────────────────────────┐
│                    约束强度递增                              │
└─────────────────────────────────────────────────────────────┘

Layer 3: Hooks 验证        ████████████████████ 最强（外部强制）
Layer 2: 结构化输出        ████████████████     中强（格式约束）
Layer 1: Prompt 纪律       ████████████         基础（自律约束）
```

---

## 二、各层对比

| 维度 | Layer 1 | Layer 2 | Layer 3 |
|------|---------|---------|---------|
| **实施难度** | ⭐ 低 | ⭐⭐ 中 | ⭐⭐⭐ 高 |
| **约束强度** | 依赖自律 | 格式可检查 | 外部强制 |
| **幻觉阻断率** | ~30-50% | ~50-70% | ~80-90% |
| **维护成本** | 低 | 中 | 高 |
| **立即可用** | ✅ 是 | ✅ 是 | 🟡 需要配置 |

---

## 三、推荐实施路径

### 阶段 1：立即实施（本周）

**Layer 1 + Layer 2 组合**

1. 更新所有 Agent 的 Prompt
   - 添加强化版工具纪律
   - 添加禁止的输出模式清单
   - 添加 BLOCKED 输出格式

2. 添加结构化输出要求
   - evidence_summary 字段
   - claims ↔ evidence 关联
   - 验证清单

**预期效果**：幻觉输出减少 50-70%

### 阶段 2：增强实施（下周）

**添加 Layer 3 Hooks**

1. 创建 `.claude/hooks/` 目录
2. 部署 track-tool-calls.py
3. 部署 validate-evidence.py（软阻断模式）
4. 观察日志，调优阈值

**预期效果**：幻觉输出减少 80-90%

### 阶段 3：严格模式（按需）

**启用硬阻断**

1. 将 validate-evidence.py 改为硬阻断
2. 添加白名单机制
3. 考虑迁移到 Agent SDK（如果需要最强约束）

---

## 四、文件清单

```
IDEA-006-implementation/
├── README.md                      # 本文件
├── layer1-prompt-discipline.md    # Layer 1 详细方案
├── layer2-structured-output.md    # Layer 2 详细方案
└── layer3-hooks-validation.md     # Layer 3 详细方案
```

---

## 五、需要修改的现有文件

### 5.1 Agent Prompt 文件

| 文件 | 修改内容 |
|------|---------|
| `Claude/agents/feature-shipper.md` | 替换工具纪律部分，添加输出格式 |
| `Claude/agents/requirement-refiner.md` | 同上 |
| `Claude/agents/code-analyzer.md` | 同上 |
| `Claude/agents/code-debug-expert.md` | 同上 |
| `Claude/agents/system-log-analyzer.md` | 保持 JSON 输出，添加 evidence 字段 |

### 5.2 新增文件

| 文件 | 用途 |
|------|------|
| `.claude/hooks/track-tool-calls.py` | 记录工具调用 |
| `.claude/hooks/validate-evidence.py` | 验证证据 |
| `.claude/settings.json` | Hooks 配置 |
| `Claude/schemas/agent-output.json` | 输出格式 Schema |

---

## 六、验收标准

### 最小验收（Layer 1+2）

- [ ] 所有 Agent Prompt 包含强化版工具纪律
- [ ] 所有 Agent 输出包含 evidence_summary
- [ ] 无证据时输出 BLOCKED 而非编造
- [ ] claims 与 evidence 有明确关联

### 完整验收（Layer 1+2+3）

- [ ] Hooks 正确配置并运行
- [ ] 工具调用被正确记录
- [ ] 输出验证能检测"声称 vs 实际"不匹配
- [ ] 幻觉输出率 < 10%

---

## 七、风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| LLM 忽略 Prompt 纪律 | Layer 3 Hooks 作为兜底 |
| Hooks 配置复杂 | 提供详细安装脚本 |
| 误报阻断正常输出 | 先用软阻断，观察调优 |
| 性能开销 | Hooks 脚本轻量化 |

---

## 八、下一步行动

1. **今天**：Review 本方案，确认实施范围
2. **明天**：修改第一个 Agent (feature-shipper) 作为试点
3. **本周**：推广到所有 Agent
4. **下周**：部署 Hooks，观察效果

---

> 核心思想：多层防守，逐步增强，从"建议"走向"强制"
