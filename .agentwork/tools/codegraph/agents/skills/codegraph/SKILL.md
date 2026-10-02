---
name: codegraph
description: 在已有 CodeGraph 索引的项目中，理解或定位代码、追调用链、排查缺陷，以及修复、新功能或重构前优先使用。先于 grep/find 或直接读取源码获取结构上下文；工具或索引不可用时回退。
---

# CodeGraph

Codex、OpenCode 与 Pi 共用的项目技能入口；Pi 同样从 `.agents/skills/` 发现本技能。

先完整读取项目内 [CodeGraph 使用规则](../../../.shared/mcp/codegraph.md)，遵循其中的「Agent 优先调用约定」。若项目存在 `.shared/patterns/semantic-navigation.md`，同时遵循其中的通用语义导航约束。

- 需要项目内的 `.codegraph/` 索引，以及 PATH 上的 `codegraph` CLI 或已连接的 CodeGraph MCP；不假设 MCP 已连接。
- 满足条件时，理解、定位或修改代码前优先使用 `codegraph_explore` 或 `codegraph explore "<symbol names or question>"` 获取相关源码、调用路径和影响范围，再读取必要文件。
- 没有索引、工具不可用或索引过期时按共享规则回退本地读取或搜索；不要把回退结果描述成 CodeGraph 输出。
- 不自动安装、初始化或接线 MCP，也不生成或修改 `.pi/settings.json` 等平台配置。
- `codegraph init`、`install`、`upgrade`、`uninit`、`uninstall` 会改变项目或机器状态，执行前说明影响并获得用户明确授权。
