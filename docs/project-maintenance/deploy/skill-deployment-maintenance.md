---
title: "Skill Deployment 维护流"
status: active
updated: 2026-04-19
owner: aw-kernel
last_verified: 2026-04-19
---
# Skill Deployment 维护流

> 目的：为当前仓库的 deploy target 提供统一的维护与诊断入口，回答“只读 `verify` 还看什么、什么时候该直接走 destructive reinstall、冲突和 drift 各怎么处理”。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)

本页只负责 deploy target 维护与诊断；首次安装看 [deploy-runbook.md](./deploy-runbook.md)，业务生命周期边界看 [skill-lifecycle.md](./skill-lifecycle.md)。

## 一、什么时候看这页

适合在下面场景先读：

- 你已经有 target root，想做日常复验
- 你怀疑 live install、target entry 或 source contract 漂移了
- 你在处理坏链路、root 类型错误、冲突目录或 unrecognized 目录
- 你想确认某个问题应该手工清理，还是直接重跑三步主流程

## 二、推荐维护循环

默认顺序固定为：

1. 需要诊断时先跑一次 `verify`
2. 需要恢复时直接跑 `prune --all -> check_paths_exist -> install`
3. 需要确认结果时再跑一次 `verify`

这个顺序的目的：

- 先区分 source 合法性问题、target root 问题和 live install drift
- 再决定是手工清冲突，还是直接按 destructive reinstall 重建
- 最后确认恢复后问题是否真的消失
- `check_paths_exist` 与 `install` 都必须做到“冲突前零业务写入”

## 三、`verify` 在看什么

### 1. 通用 `verify`

用途：

- 检查 deploy target root 是否存在、是否是目录、是否是坏链路
- 检查 payload source 是否齐全、target path metadata 是否留在 backend target root 内，且没有 source drift
- 检查 live install 的 target entry、required payload files 与当前 source 是否仍对齐
- 检查 target root 下是否存在 conflict / unrecognized 目录
- 检查 runtime `aw.marker` 是否仍能把目录识别为当前 backend 的受管安装物

执行入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

如果 backend 需要显式 root override，例如 `agents` 的 `--agents-root`，就在命令上附加对应参数。参数来源见 [Codex Usage Help](../usage-help/codex.md)。

如果手工改过 target root，导致它不是目录，`verify` 会把它报成结构错误。
如果手工改过已安装 skill 目录中的同步文件，`verify` 会把它报成 live install drift 或 required payload 缺失。

## 四、恢复主流程

只读检查：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

需要恢复时，直接走三步主流程：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
```

当前三步的维护语义：

- `prune --all` 只删除当前 backend 受管、且带可识别 marker 的目录
- `check_paths_exist` 只做全量冲突扫描；任何冲突都必须由 operator 先处理
- `install --backend agents` 只写当前 source 声明的 live payload；不会做 archive / history、增量修复或旧版本保活
- `.agents/` 或其他 target root 不是 canonical truth；恢复动作不能反向把 target 当 source 改

## 五、故障信号怎么路由

| 信号或症状 | 常见含义 | 优先处理方式 |
|---|---|---|
| `missing-target-root` | target root 还没建立，或已有 root 被删了 | 直接走三步主流程重建 |
| `wrong-target-root-type` | target root 存在，但不是目录 | 修正 root 后重跑三步主流程 |
| `broken-target-root-symlink` | target root 是坏链路 | 删除坏链路后重跑三步主流程 |
| `missing-backend-payload-source` / `missing-required-payload` | source layer 缺件，deploy 读取面不完整 | 回到 `product/harness/adapters/agents/skills/` 修正 payload source |
| `missing-canonical-source` | payload 指向的 canonical source 丢失或 canonical file 缺失 | 修正 `product/harness/skills/` 后再重装 |
| `payload-contract-invalid` | payload descriptor 自身字段、路径或 target contract 不一致 | 先修 source contract，再走三步主流程 |
| `payload-policy-mismatch` / `reference-policy-mismatch` | payload descriptor 的策略字段偏离当前 contract | 先修 payload source，再走三步主流程 |
| `duplicate target_dir` | 当前 source 把多个 live skill 指到同一目标目录 | 这是 source 非法；修 source，不能靠 install 猜测覆盖 |
| `check_paths_exist` 冲突清单 | 当前 source 解析出的目标路径已存在 | 先由 operator 清理冲突目录，再从 `prune --all` 重跑 |
| `unrecognized-target-directory` | 目录存在，但没有可识别 marker，或 marker 不能证明它属于当前 backend 受管 install | 不让脚本猜测处理；先手工改名、删除或确认保留 |
| `unexpected-managed-directory` | target root 下残留了带可识别 marker、但已不在当前 source live bindings 里的受管目录 | 先执行 `prune --all` 清掉旧受管目录，再按三步主流程重装 |
| `missing-target-entry` / `missing-required-payload` | live install 缺 entry 或缺必需文件 | 先看是否 drift，再重跑三步主流程 |
| `target-payload-drift` | 已安装 payload 与当前 source 不一致 | 直接走三步主流程恢复 |

## 六、额外判断

如果 `verify` 失败，但 `check_paths_exist` 通过：

- 更可能是 target root 结构问题或 live payload drift
- 先修对应问题，再重跑三步主流程

如果 `check_paths_exist` 失败，但 `verify` 没有明显 drift：

- 更可能是 foreign / unrecognized 目录占住了当前 live target path
- 先手工清理冲突，再重跑三步主流程
