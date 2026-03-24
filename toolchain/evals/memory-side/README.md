# Memory Side Evals

`toolchain/evals/memory-side/` 保存 `Memory Side` 主题下的基础测试提示、关键问题列表和测试评分规则，不保存业务源码和运行期产物。

当前主线：

- `program.md`
- `scenarios.json`
- `schemas/`
- `scoring/`

AI 先读什么：

1. `toolchain/evals/README.md`
2. `program.md`：基础测试提示
3. `scenarios.json`：关键问题列表
4. 需要看记录格式和测试评分时，再读 `schemas/` 与 `scoring/`

当前 `scoring/` 的最小覆盖面包括：

- `knowledge-base-rubric.json`
- `context-routing-rubric.json`
- `writeback-cleanup-rubric.json`

暂时不要先读什么：

- `.autoworkflow/` 里的运行结果
- `product/` 下的业务源码，除非当前任务要交叉验证评测对象

这里适合放：

- 基础测试提示
- 关键问题列表
- 测试记录格式
- 测试评分规则

这里不适合放：

- 运行日志
- 临时结果
- 项目主线规则
