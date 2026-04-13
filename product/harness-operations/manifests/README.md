# Manifests

本目录预留给 `Harness Operations` 的全局安装、打包和市场分发元数据。

当前阶段：

- 业务源码仍在 `product/harness-operations/skills/` 与 `product/harness-operations/adapters/`
- repo-local 测试挂载点仍在 `.claude/`、`.agents/` 与 `.opencode/`
- 部署行为由 `toolchain/scripts/deploy/adapter_deploy.py` 统一处理
- `harness.template.yaml` 是 canonical harness runtime/init 模板
- `harness-template.deferred-issues.md` 记录已确认但暂缓处理的 manifest/runtime 合同问题
- `toolchain/scripts/deploy/init_harness_project.py` 负责把模板实例化到 repo-local 或自定义 harness 路径
