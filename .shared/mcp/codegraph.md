# CodeGraph Reference

该文件是 codegraph 可选工具的引用型参考文档：只记录官方接入路径，不 vendor 上游源码或二进制。

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

查询由 agent 按项目导航约定选择 CLI 或已连接的 MCP；索引随文件变更自动同步。

CLI 或项目索引缺失时回退本地读取/搜索；任务确实需要图谱时可提出建索引建议，经用户授权后运行 `codegraph init`。

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
