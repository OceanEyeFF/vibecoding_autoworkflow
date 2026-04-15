---
title: "Skill 生命周期维护"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Skill 生命周期维护

> 目的：说明当前 deploy 接口不承接 skills / `.aw_template/` 的业务生命周期，只承接 runtime target root 端点。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Deploy Runbook](./deploy-runbook.md)

## 一、适用范围

本页适合在下面场景先读：

- 你在改 skill source
- 你在改 `.aw_template/`
- 你在判断某个业务变化是否需要 deploy 跟进

本页不负责：

- drift 故障诊断展开
- canonical skill 合同正文

## 二、Source of Truth 与 Deploy Target 边界

固定边界：

- source of truth 在 `product/`
- 当前 deploy target 只在 `.agents/` 或对应 global root
- `docs/harness/` 负责 Harness-first doctrine、workflow family 与 adjacent-system 主入口

因此：

- 改 skill 内容时先改 `product/`
- 当前 deploy 不会读取 skill 内容，也不会同步 skill 目录
- 只有已经验证过的 root 状态，才写回 `docs/`
- 若出于 repo-local 安装兼容、文件分发或运行试验需要，`.agents/skills/` 可以承接 tracked install payload；但这不属于当前 deploy 接口的职责

## 三、当前执行边界

- 当前 deploy 接口只管理 runtime target root
- 它不定义 skills 的 source 映射
- `.aw_template/` 与 canonical skills 的映射仍待后续重定

因此当你修改 skills / `.aw_template/` 时：

- 不要把 deploy 文档当成业务同步方案
- 不要把 deploy target 当 source 去改
- 如果只是要确保 runtime root 存在，再走 `local/global`

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
- 在业务映射还没定的时候，把 source 组织方案提前写死在 deploy 工具里
