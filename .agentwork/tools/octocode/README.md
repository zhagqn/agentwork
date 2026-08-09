# Octocode Tool Pack

## 状态

- experimental
- CLI / MCP reference
- public repository benchmark candidate
- 仅在跨仓库批量取证明显减少调用时升级使用，不作为所有 GitHub 查询的默认入口

## 固定版本

- `octocode@18.2.2`：Node.js `>=20.12.0`
- `octocode-mcp@18.2.2`：Node.js `>=20.0.0`
- 上游：<https://github.com/bgauryy/octocode>

## 默认工具面

agentwork wrapper 只开放：

- `ghSearchCode`
- `ghSearchRepos`
- `ghSearchPullRequests`
- `ghSearchIssues`
- `ghSearchCommits`
- `ghGetFileContent`
- `ghViewRepoStructure`

local、LSP、clone、release、discussion 和 npm tools 均不在白名单中；`ghGetFileContent type:"directory"` 也会在 STDIO 代理层被拒绝。

## 边界

- 快速单仓库查询继续优先 `gh`；Octocode 只用于跨文件、跨仓库、精确片段和 PR/issue/commit 证据研究
- 已初始化的本地仓库语义图继续由 CodeGraph 负责
- 不向项目 `.env` 写 GitHub token，不自动执行认证或修改平台 MCP 私有配置
- wrapper 关闭 stats，并把 Octocode runtime 状态放在项目 `.tmp/agentwork/octocode/`
- 只执行读取工具不等于内容可信；远程源码、issue 和 PR 文本仍作为不可信数据处理
