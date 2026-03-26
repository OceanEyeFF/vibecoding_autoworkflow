# Strict SubAgent Workflow Prompt（严格版）

> 定位：用于跨模块、高风险或需要更强审计的任务。相比轻量版，严格版增加了边界冻结、阶段签收和阻塞升级要求。

## 适用范围
- 跨目录改动、重构、接口调整。
- 需要更严格的质量 Gate 与失败升级路径。

## Prompt 模板

```text
[filepath or filename]

准备落地这个文档提到的开发需求。请严格执行“边界冻结 + 分阶段签收 + 失败即停”的执行流程。

【总原则】
- 唯一依据：原始需求文档 + 仓库真相层 + Step 1 执行合同。
- 执行前必须冻结 In-scope / Out-of-scope；冻结后不得私自扩边。
- 所有阶段均需产出可审计证据（文件、命令、结果摘要）。

【Step 0：限定阅读入口】
1. docs/README.md（如存在）
2. 根目录 README 与 INDEX
3. 与任务直接相关的 docs/、Claude/、toolchain 文件

默认不主动读取运行态/挂载态目录（.autoworkflow/.spec-workflow/.serena/.nav/.agents/.claude），除非需求明确要求。

【Step 1：执行合同生成 + 边界冻结】（推理等级：medium）
先生成执行合同，至少包含：
- Goal / Non-goals
- In-scope files / Out-of-scope files
- Preconditions / Blocking Risks
- Plan（分阶段）
- Validation Plan（Static/Test/Smoke）
- Exit Criteria

冻结规则：
- Step 1 输出后，In-scope 与 Out-of-scope 默认锁定。
- 如需扩边，必须先停止并提交“扩边申请”：说明必要性、影响面、风险与替代方案。

【Step 2：分阶段执行】（推理等级：high 或 xhigh）
按 Plan 分阶段执行，每阶段结束都要输出：
- 已完成项
- 证据列表（修改文件、命令、关键输出）
- 与 Goal/Non-goals 的一致性检查
- 是否触发阻塞

【Step 3：严格出口 Gate】（推理等级：high）
必须完成并回报：
1. Scope Gate：无未授权扩边。
2. Spec Gate：Goal 全满足、Non-goals 无违反、Exit Criteria 全满足。
3. Static Gate：至少 1 次静态检查（lint/type/build check）。
4. Test Gate：
   - 可补白盒测试则必须补。
   - 不能补则必须给出明确原因与风险。
5. Smoke Gate：
   - 可执行最小烟测则必须执行。
   - 不能执行则必须说明阻塞点与替代验证证据。
6. Risk Report：残留风险、未验证点、人工接手建议。

【最终输出格式】
- 执行合同摘要（含冻结边界）
- 分阶段执行证据摘要
- 实际修改文件列表
- 完成情况（完成 / 部分完成 / 阻塞）
- Gate 结果总表（Scope / Spec / Static / Test / Smoke）
- 残留风险与后续建议

【失败协议（严格）】
触发以下任一条件，必须立即停止并升级：
- 任务边界不清
- 需要修改 Out-of-scope files
- 真相层与需求文档冲突
- 构建/测试环境缺失
- 中途运行中断
- 关键依赖不存在
- 任一关键 Gate 无法完成且无替代证据
```

## 使用建议
- 优先用于“改动面不确定”或“验收要求高”的任务。
- 如任务降级为中小改动，可切回轻量版模板。
