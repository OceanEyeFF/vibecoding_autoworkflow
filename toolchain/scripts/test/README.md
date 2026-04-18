# Governance Checks

`toolchain/scripts/test/` 保存轻量治理检查入口。

当前主线：

- `folder_logic_check.py`：检查根目录分层、一级目录白名单、hidden/state/mount layer 例外白名单，以及 `docs/` / `toolchain/` 下的错位内容
- `path_governance_check.py`：检查 markdown 相对链接、关键主入口、路径/文档治理回链、`docs/project-maintenance/`、`docs/harness/` 与 `docs/autoresearch/` 主线入口完整性、正文文档 frontmatter、目录状态约束和 `.gitignore` 中的关键 hidden-layer 忽略项
- `governance_semantic_check.py`：检查关键模板是否存在、关键知识页是否回链承接模板、canonical skill 包体是否保持最小 executable shape、adapter 层是否没有重新长出错误的 wrapper 真相、foundations 权威文档是否出现影子文件，以及已退役的占位口径是否回流
- `agents_first_wave_smoke.py`：在隔离 install root 和生成的 `.aw` fixture 上，证明 `agents` first-wave payload 可读取，并且 `harness -> repo-status -> repo-whats-next -> init-worktrack -> dispatch` 的最小 contract 路径成立；它不宣称真实 `SubAgent` dispatch 或 autonomy loop 已经落地
- `scope_gate_check.py`：按 contract 中的 `in_scope` / `out_of_scope` 规则校验本轮改动是否越界
- `gate_status_backfill.py`：把 gate 结果回填到 `.autoworkflow/state/` 和 closeout 摘要
- `governance_assess.py`：对 `rule / folders / document / code` 四维输入做最小治理收口评估
- `repo_governance_eval.py`：对五维 repo maintainability 输入做总分、评级和 AI compatibility 评估

适用场景：

- 文档入口刚调整过
- foundations 合同刚更新过
- 需要给 harness closeout 或 repo audit 生成结构化治理评估
- 想快速确认 AI 的默认读取主线没有被新改动破坏

不要把下面这些东西放进这里：

- CI 平台配置
- 重型 lint 框架
- 与路径治理无关的大型测试逻辑
