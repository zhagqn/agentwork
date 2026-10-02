# CodeGraph Reference

该文件随 codegraph 可选工具安装，记录项目级导航约定与官方接入路径，不 vendor 上游源码或二进制。

- 上游：<https://github.com/colbymchenry/codegraph>（MIT）
- 定位：本地预建代码知识图谱，提供 CLI 与可选 MCP server，用于符号、跨文件调用路径和影响范围查询，文件变更自动增量同步
- 免责：本文档若与官方仓库最新说明不一致，以官方为准

## 收益边界（如实标注）

- 上游基准在其选定的仓库、任务与模型下测得工具调用和成本下降，不代表所有项目都有同样收益。
- 跨模块结构查询通常更值得评估；已知路径的小改动可能直接 read/grep 更轻量（[上游 issue #1080](https://github.com/colbymchenry/codegraph/issues/1080) 提供了小任务变慢的用户反馈）。
- 在实际项目中比较任务质量、耗时、工具调用与计费成本，不只比较 token 数。

## 安装流程

CLI 导航需要本机 CLI 与项目索引；MCP 接线按使用的 Agent 另行选择：

```bash
# 1. 安装 CLI（自带 runtime，不要求本机 Node）
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
# 或已有 Node 时：npm i -g @colbymchenry/codegraph

# 2. 每个项目单独建索引（创建 .codegraph/ 并开启文件监听自动同步）
cd <project>
codegraph init

# 3. 验证 CLI 查询，无需 MCP
codegraph explore "<symbol names or question>"
```

需要 MCP 时再运行 `codegraph install`，选择目标 Agent 和项目级作用域。该命令会修改 Agent 配置与指令，部分平台还会设置工具自动许可；执行前说明这些影响并取得授权。仅使用 CLI 的 Pi 无需这一步。具体参数以已安装版本的 `codegraph install --help` 为准。

- 升级：`codegraph upgrade`（`--check` 仅查询）
- Claude Code 验证：`/mcp` 中确认 codegraph server 已连接
- Codex 验证：`codex mcp list` 中确认 codegraph 存在

## 日常使用

### Agent 优先调用约定

- 本约定只随可选工具安装到目标项目，不加入核心 bootstrap 或用户级全局约束。
- 目标项目存在 `.codegraph/`，且当前会话有 CodeGraph MCP 或本机 `codegraph` CLI 可用时，在理解、定位或准备修改代码（排查缺陷、修复、新功能、重构）时优先查询 CodeGraph，再补充普通读取/搜索。已知文件或符号同样适用，不必等普通搜索失败。
- MCP 使用 `codegraph_explore`；未连接 MCP 但 CLI 可用时，从目标项目根目录执行 `codegraph explore "<symbol names or question>"`。查询中带上相关符号或路径，获取源码、调用链及影响范围；不要自动补装 MCP 来代替可用 CLI。
- 工具或索引缺失时，本轮该项目直接回退读取/搜索，不反复调用失败入口，不把普通搜索描述为 CodeGraph 结果。建索引是用户决定；不要仅因本规则自动安装 CLI、初始化索引、升级或修改平台配置。
- 文件监听进程正常运行时，索引会增量同步。若查询提示过期或同步停止，直接读取受影响文件核实当前内容；需要刷新时说明 `codegraph sync` 的用途，不把旧图谱当作当前源码。没有过期或缺失提示时，不机械重复读取已返回的源码。
- 配置、文档、图谱未覆盖的内容仍可直接读取。跨文件解析可能有歧义，正确性仍由编译器、测试和 lint 验证。

### 项目级入口与生效边界

| 平台 | 随工具安装的入口 | 触发方式 |
| --- | --- | --- |
| Codex / OpenCode / Pi | `.agents/skills/codegraph/SKILL.md` | 三者共用一份技能；通过技能描述匹配代码任务，加载后执行本约定；Pi 需先信任项目 |
| Claude Code | `.claude/rules/codegraph.md` | 无 paths 限制的项目规则；满足工具与索引条件后触发 |
| Cursor | `.cursor/rules/codegraph.mdc` | alwaysApply 项目规则；满足工具与索引条件后触发 |

这些入口提供模型可读取的优先调用指令，不是强制拦截器；技能选择、项目信任和资源重载由平台运行时决定。安装后在目标项目重新加载技能或开启新会话，并通过实际工具调用确认生效。没有自动查询、索引维护或 MCP 连接保证。

依据：CodeGraph `v1.6.0` 官方 [Agent 指令](https://github.com/colbymchenry/codegraph/blob/v1.6.0/src/installer/instructions-template.ts) 与 [MCP 指令](https://github.com/colbymchenry/codegraph/blob/v1.6.0/src/mcp/server-instructions.ts)；平台发现机制见 [Codex skills](https://developers.openai.com/codex/skills/)、[OpenCode skills](https://opencode.ai/docs/skills/)、[Pi skills](https://github.com/earendil-works/pi/blob/v0.84.4/packages/coding-agent/docs/skills.md)、[Claude rules](https://code.claude.com/docs/en/memory)、[Cursor rules](https://cursor.com/docs/context/rules)。

## 遥测

默认开启匿名用量统计（不含代码、路径、符号名、查询、IP；安装器会询问）。关闭方式任选：

```bash
codegraph telemetry off
# 或环境变量：CODEGRAPH_TELEMETRY=0 / DO_NOT_TRACK=1
```

## 资源与卸载

- `codegraph init` 后有常驻文件监听进程做增量索引；大仓库注意磁盘/CPU 占用，不用时按项目 `codegraph uninit`
- `.codegraph/` 属项目本地索引，默认不纳入提交
- 完全卸载：`codegraph uninstall`（移除所有 agent 接线和 CLI；`--keep-cli` 只移除接线）

## 与 agentwork 约束的关系

- `.shared/patterns/semantic-navigation.md` 要求语义查询优先；平台自带能力不足或需要跨文件调用图时，codegraph 是一个可选的具体实现
- 与 ponytail 组合：codegraph 收敛读路径（发现成本）、ponytail 收敛写路径（生成成本），两者正交；codegraph 还让 ponytail"复用已有代码"一级在大仓库里可低成本执行
- 是否启用属于平台层决策，agentwork 不预装、不默认开启
