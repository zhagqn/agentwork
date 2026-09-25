---
name: codegraph
description: 在已有 CodeGraph 索引的项目中，理解或定位代码、追调用链、排查缺陷，以及修复、新功能或重构前优先使用。先于 grep/find 或直接读取源码获取结构上下文；工具或索引不可用时回退。
compatibility: Requires a project-local .codegraph index and either the codegraph CLI on PATH or connected CodeGraph MCP tools; MCP connectivity is optional and not assumed.
---

# codegraph

Pi 项目级 CodeGraph 技能入口。

## 执行前必读

- 完整读取本 tool pack 随附的参考：`../../../.shared/mcp/codegraph.md`
- 若项目存在 `.shared/patterns/semantic-navigation.md`，同时遵循其中的通用语义导航约束。

## 使用边界

1. 遵循参考中的「Agent 优先调用约定」：先确认目标项目存在 `.codegraph/`，且当前会话有 CodeGraph MCP 或本机 CLI 可用。
2. 理解、定位或修改代码前，优先使用 `codegraph_explore` 或 `codegraph explore "<symbol names or question>"`；根据结果再读取必要文件。
3. 不假设 Pi 已连接 CodeGraph MCP，也不生成或修改 `.pi/settings.json`。
4. 工具或索引缺失时回退 Pi 的本地读取/搜索；索引过期时直接读取受影响文件。不要把回退结果描述成 CodeGraph 输出。
5. `codegraph init`、`install`、`upgrade`、`uninit`、`uninstall` 会改变项目或机器状态，执行前说明影响并获得用户明确授权。
