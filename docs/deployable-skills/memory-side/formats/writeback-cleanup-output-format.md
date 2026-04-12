---
title: "Writeback & Cleanup 输出格式"
status: active
updated: 2026-03-20
owner: aw-kernel
last_verified: 2026-03-20
---
# Writeback & Cleanup 输出格式

> 目的：为 `Writeback & Cleanup` 规定固定输出格式，避免不同 AI 后端在任务收尾时产出风格差异很大的回写说明。

## 一、输出对象

`Writeback & Cleanup` 的标准输出对象叫 `Writeback Card`。

它是当前任务的最小回写与清理卡片，不是完整复盘，也不是完整变更日志。

## 二、固定字段

### 必填字段

```text
task:
verified_changes:
non_changes:
write_to_core_truth:
write_to_operational_truth:
do_not_write_back:
cleanup_targets:
risks_left:
verification_basis:
```

### 选填字段

```text
write_to_exploratory_records:
followups:
docs_to_sync:
notes_for_next_round:
```

## 三、字段含义

- `task`
  当前任务的简短描述。

- `verified_changes`
  本轮已经被验证成立的变更事实。

- `non_changes`
  本轮明确没有变化的边界，用来防止后续误读。

- `write_to_core_truth`
  需要进入主线长期真相层的内容。

- `write_to_operational_truth`
  需要进入当前运行真相层的内容，例如状态、风险、近期变更、后续动作。

- `do_not_write_back`
  当前不能写回仓库主线的内容。

- `cleanup_targets`
  需要清理、降级、标记过期或更新入口的旧内容。

- `risks_left`
  任务结束后仍保留的风险和未解点。

- `verification_basis`
  支撑本轮回写决策的验证依据。

- `write_to_exploratory_records`
  如果有必要保留分析过程，可写明应放入探索记录层的内容。

- `followups`
  后续还需要继续推进的动作。

- `docs_to_sync`
  需要同步更新的文档入口清单。

- `notes_for_next_round`
  给下一轮 AI 的最小交接信息。

## 四、格式约束

- 优先写事实，不写长篇总结
- 每个字段都尽量短而明确
- `verified_changes` 和 `verification_basis` 必须能互相对应
- `do_not_write_back` 不能留空，至少要明确排除临时推理或未验证判断
- 如果回写目标不明确，优先列入 `followups` 或 `notes_for_next_round`

## 五、推荐模板

下面模板使用的是当前推荐目录布局，只是示例，不代表所有目标仓库都必须逐字采用同一路径。

```text
task: 为目标仓库补充 Context Routing 的固定输出格式。
verified_changes:
- 已新增 Context Routing 输出格式文档
- 已定义 Route Card 的固定字段和模板
non_changes:
- 未调整宿主调用层设计
- 未引入 retrieval 或外部数据库
write_to_core_truth:
- Context Routing 的标准输出对象为 Route Card
- Route Card 需要包含固定字段集合
write_to_operational_truth:
- 本轮已完成 Context Routing 文档组初版
- 后续需要继续补 Writeback & Cleanup 文档组
do_not_write_back:
- 对未来宿主调用层形态的未验证猜测
- 对不同后端细节优化的临时想法
cleanup_targets:
- 仍把 Context Routing 描述成泛化交互模块的旧表述
- 未链接到输出格式文档的旧入口
risks_left:
- 各仓库的具体回写落点还没有项目级规则
verification_basis:
- 已新增文档并与基线页建立索引关系
write_to_exploratory_records:
- 不同后端的提示词微调方向
followups:
- 起草 Writeback & Cleanup 的规则文档、Prompt 和输出格式
docs_to_sync:
- docs/deployable-skills/memory-side/context-routing.md
- docs/deployable-skills/memory-side/overview.md
notes_for_next_round:
- 下一轮应优先补任务结束后的文档回写规则
```

## 六、判断标准

如果下面几句话成立，说明输出格式是合格的：

- 不同后端能产出结构接近的 `Writeback Card`
- 执行端可以据此直接做文档回写
- 回写说明能区分“应写回的事实”和“不应进入主线的噪声”
