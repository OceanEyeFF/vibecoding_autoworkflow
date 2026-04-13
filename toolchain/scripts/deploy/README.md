# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：把 `product/` 下的 adapter 源码部署到 repo-local mount 或全局技能目录，并提供 deploy target 校验与清理能力
- `init_harness_project.py`：从 canonical harness 模板初始化 runtime 目录和 `harness.yaml`

最小维护流：

1. 先跑 `sync verify`
2. 再跑 `local` 或 `global` 部署
3. 最后再跑一次 `sync verify`
4. 如 backend 支持，再补 `smoke verify`

额外说明：

- `sync verify` 由 `adapter_deploy.py verify` 提供，用于检查缺失 mount、陈旧 target、坏链路和错误路径类型
- `init_harness_project.py` 只负责 harness runtime/init，不改 adapter wrapper，也不组装 `SKILL.md`
- `smoke verify` 是 backend-specific 的最小可用性确认，不属于 deploy 脚本本身
- 当前 `smoke verify` 只对 `agents` 与 `claude` 建立口径，`opencode` 仍停在 `sync verify`
- `--prune` 用于在部署时清理已经没有 source 对应关系的 target
- 该目录只负责部署维护，不负责 research runner

回归测试入口：

```bash
python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

当前测试覆盖：

- local / global 首次部署到空 target
- source 更新后的重新部署
- source 删除后的 drift 检测、`--prune` 清理与复验
- `verify` 的 missing / unexpected / broken symlink / wrong type 结构错误
