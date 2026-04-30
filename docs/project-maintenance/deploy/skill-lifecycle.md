---
title: "Skill 生命周期维护"
status: active
updated: 2026-05-01
owner: aw-kernel
last_verified: 2026-05-01
---
# Skill 生命周期维护

> 目的：说明当前 deploy 接口不承接 skills / `.aw_template/` 的业务生命周期决策。它只消费已经冻结的 source layer，并通过 destructive reinstall 把当前 live payload 写入 target root。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Deploy Runbook](./deploy-runbook.md)
- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Template Consumption Spec](./template-consumption-spec.md)

## 一、适用范围

本页适合在下面场景先读：

- 你在改 skill source
- 你在改 `.aw_template/`
- 你在判断某个业务变化是否需要 deploy 跟进

本页不负责：

- drift（偏离）故障诊断展开
- canonical skill 合同正文

## 二、Source of Truth 与 Deploy Target 边界

固定边界：

- source of truth（唯一真相来源）在 `product/`
- 当前 deploy target 是 backend 解析出的 skills root
- `docs/harness/` 负责 Harness-first doctrine、workflow family 与 adjacent-system 主入口
- canonical source 到 target entry 的正式映射规则见 [Deploy Mapping Spec](./deploy-mapping-spec.md)

因此：

- 改 skill 内容时先改 `product/`
- 当前 deploy 不会把 `.aw_template/` 当 deploy payload source（部署负载来源），也不会把它直接发往 target
- `.aw_template/` 的 `.aw/` 目录结构、管理文档模板和待迁移模板边界见 [Template Consumption Spec](./template-consumption-spec.md)
- 只有已经验证过的 root 状态，才写回 `docs/`
- 当前 backend skills root 是 ignored repo-local deploy target；不得承接 tracked install payload，也不是 truth owner

## 三、当前执行边界

- 当前 deploy 接口对 `agents` 生效，并对 `claude` 提供完整 Harness skill payload set
- 主流程固定为 `prune --all -> check_paths_exist -> install --backend <backend>`
- `install --backend <backend>` 只消费当前 live payload descriptor，并把 canonical skill copy、payload descriptor 与 runtime-generated `aw.marker` 写入当前 backend 的 resolved target root
- `verify --backend <backend>` 只读检查 source layer、live install drift，以及 conflict / unrecognized 目录
- `prune --all` 只删除带可识别、且属于当前 backend 的受管 marker 目录
- `check_paths_exist` 只做冲突扫描；任何冲突都必须在写入前失败
- skills 的 canonical source、backend payload source、部署负载规则与 verify 口径，见 [Deploy Mapping Spec](./deploy-mapping-spec.md)
- `.aw_template/` 当前只在 deploy 文档里作为 `.aw/` 目录结构与运行管理文档模板的来源出现，不作为 deploy source，也不自动证明其中模板的最终 owner

因此当你修改 skills / `.aw_template/` 时：

- 不要把 deploy 文档当成业务同步方案
- 不要把 deploy target 当 source 去改
- 如果只是要让 live install 重新对齐 source，就走三步主流程
- 如果 source 中出现重复 `target_dir`，这是 source contract 违规，必须先修 source；不能让 install 猜测覆盖
- 如果 skill 被移除、改名或换 `target_dir`，operator-facing 语义都是同一件事：清掉我方受管旧安装，再按当前 live bindings 重装，不保留旧版本
- 不存在“先确认新目录可用，再删旧目录”的主流程承诺；删除与重装是显式分开的 destructive reinstall
- 如果 shared mount 上已经有同名目录但没有可识别 marker，脚本不会接管它；需要先由 operator 做显式迁移决策
- 不要把“如果未来允许 nested target_dir 会怎样”提前当成当前 lifecycle bug；那属于 contract expansion，不属于当前单层 target 模型

## 四、重新扩展接口前先做什么

如果后续要重新引入：

- 新 backend
- `.aw_template/` 到 skills 的稳定映射
- 新的 source provider / overlay 结构

先做这些事，再扩 deploy：

- 固定新的 target contract
- 固定 canonical source 与 install payload 的边界
- 同步更新 `docs/project-maintenance/deploy/` 和对应测试

## 五、常见误区

- 把 `.agents/` 下的 install payload 当 source of truth，反向压过 `product/`
- 把当前 deploy 脚本误当成 skills / `.aw_template` 的业务同步器
- 把 destructive reinstall 误写成 archive/history、增量修复或旧版本保活
- 试图让脚本自动接管无 marker 或 foreign 目录
- 在业务映射还没定的时候，把 source 组织方案提前写死在 deploy 工具里
