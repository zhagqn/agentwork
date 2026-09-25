---
name: codegraph
description: 在已有 CodeGraph 索引的项目中，理解或定位代码、追调用链、排查缺陷，以及修复、新功能或重构前优先使用。先于 grep/find 或直接读取源码获取结构上下文；工具或索引不可用时回退。
---

# CodeGraph

先读取项目内 [CodeGraph 使用规则](../../../.shared/mcp/codegraph.md)，遵循其中的「Agent 优先调用约定」。

- 项目存在 `.codegraph/` 且当前会话有 CodeGraph MCP 或本机 CLI 可用时，优先使用 `codegraph_explore` 或 `codegraph explore` 获取相关源码、调用路径和影响范围。
- 没有索引、工具不可用或索引过期时按共享规则回退；不要自动安装、初始化或接线 MCP。
