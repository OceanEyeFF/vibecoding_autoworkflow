# Governance Checks

`toolchain/scripts/test/` 保存轻量治理检查入口。

当前主线：

- `path_governance_check.py`：检查 markdown 相对链接、关键主入口、路径治理回链和 `.gitignore` 中的关键 hidden-layer 忽略项

适用场景：

- 文档入口刚调整过
- foundations 合同刚更新过
- 想快速确认 AI 的默认读取主线没有被新改动破坏

不要把下面这些东西放进这里：

- CI 平台配置
- 重型 lint 框架
- 与路径治理无关的大型测试逻辑
