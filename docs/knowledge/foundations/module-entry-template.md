---
title: "Module Entry 模板"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Module Entry 模板

> 目的：给 repo 模块入口页提供固定骨架，只回答“这个模块是什么、归谁、先读哪层”。

## 一、固定字段

- `module`
- `positioning`
- `owns`
- `does_not_own`
- `entrypoints`
- `read_when`
- `read_after`
- `related_layers`

## 二、模板

```md
# [Module Name] 模块总览

## module

- [模块名]

## positioning

- [它是什么]
- [它不是什么]

## owns

- [本模块拥有的主线语义]

## does_not_own

- [本模块不拥有的语义]

## entrypoints

- [稳定入口页]
- [实现入口]
- [runbook 入口]

## read_when

- [什么问题先读本模块]

## read_after

1. [先读什么]
2. [再读什么]

## related_layers

- [knowledge / operations / analysis / toolchain / state 的映射]
```
