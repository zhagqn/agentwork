# CodeGraph MCP Reference

该文件是 codegraph 可选工具的引用型参考文档：只记录官方接入路径，不 vendor 上游源码或二进制。

- 上游：<https://github.com/colbymchenry/codegraph>（MIT）
- 定位：100% 本地的预建代码知识图谱 + MCP server——把 grep/glob/Read 的多轮试探收敛为一次语义查询（符号、跨文件调用路径含动态分发、影响范围），文件变更自动增量同步
- 免责：本文档若与官方仓库最新说明不一致，以官方为准

## 收益边界（如实标注）

- 确定收益是**更少工具调用、更快回答**（官方基准：工具调用 -40%~-81%）
- token / 成本收益**规模依赖**：大而复杂的仓库、高频调用场景才显著；小任务上直接 read/grep 更轻量时可能不降反升（上游 issue #1080 跟踪工具选择问题）
- 比较成本请看 cost 而非 token 计数：其响应大部分体积是低价 cache read

## 安装流程

三步职责不同，缺一不可：

```bash
# 1. 安装 CLI（自带 runtime，不要求本机 Node）
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
# 或已有 Node 时：npm i -g @colbymchenry/codegraph

# 2. 接线 agent（新终端执行；自动检测 Claude Code / Codex / Cursor 等并写入 MCP 配置）
codegraph install

# 3. 每个项目单独建索引（创建 .codegraph/ 并开启文件监听自动同步）
cd <project>
codegraph init
```

- 升级：`codegraph upgrade`（`--check` 仅查询）
- Claude Code 验证：`/mcp` 中确认 codegraph server 已连接
- Codex 验证：`codex mcp list` 中确认 codegraph 存在

## 日常使用

**用户层零调用**：查询由 agent 自行决定何时调用 MCP 工具，索引随文件变更自动同步，无需重跑。用户唯一要做的是每个新项目一次 `codegraph init`。

**助手职责（降低用户心智负担）**：本参考文档已安装的项目里，若助手发现 codegraph CLI 可用但当前项目缺 `.codegraph/`，应主动提出运行 `codegraph init`（属安装型操作，先确认再执行），而不是等用户想起来。忘记 init 也不是故障：agent 查不到图谱时自然退回 grep/Read，只是慢一点。

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
