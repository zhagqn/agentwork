---
name: codegraph
description: Use an existing local CodeGraph CLI and project index for semantic code navigation, symbol lookup, call paths, and impact analysis. Use when a Pi task needs deeper repository navigation than direct read or grep can provide.
compatibility: Requires the codegraph CLI on PATH and an existing project-local .codegraph index; MCP connectivity is optional and not assumed.
---

# codegraph

Pi 项目级 CodeGraph 技能入口。

## 执行前必读

- 完整读取本 tool pack 随附的参考：`../../../.shared/mcp/codegraph.md`
- 若项目存在 `.shared/patterns/semantic-navigation.md`，同时遵循其中的通用语义导航约束。

## 使用边界

1. 先确认当前仓库存在 `.codegraph/`，并且 `codegraph` CLI 可用。
2. 满足条件时优先执行 `codegraph explore "<symbol names or question>"`；根据结果再读取必要文件。
3. 不假设 Pi 已连接 CodeGraph MCP，也不生成或修改 `.pi/settings.json`。
4. CLI 或索引缺失时，直接回退 Pi 的本地读取/搜索能力；不要把回退结果描述成 CodeGraph 输出。
5. `codegraph init`、`install`、`upgrade`、`uninit`、`uninstall` 会改变项目或机器状态，执行前说明影响并获得用户明确授权。
