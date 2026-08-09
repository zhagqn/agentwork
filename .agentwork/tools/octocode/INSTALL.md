# Install Octocode Tool

## What gets installed

- `.shared/mcp/octocode.md`
- `.shared/scripts/octocode-mcp.py`

不会安装全局 package、写 GitHub token、创建 `.env` 或修改平台 MCP 私有配置。

## Install

```bash
python3 install-tool.py install octocode -p <path>
python3 install-tool.py -i octocode -p <path>
```

## Authentication

Octocode 18.2.2 的 GitHub 工具需要认证。优先复用已有 GitHub CLI 登录：

```bash
gh auth status
```

未登录时由用户自行运行 `gh auth login`。不要把 token 写入项目 `.env` 或对话；上游会在无 token 环境变量和 Octocode 凭据时回退 `gh auth token`。

## Verify

```bash
python3 .shared/scripts/octocode-mcp.py --check
```

然后按 `.shared/mcp/octocode.md` 手动接入 MCP client，并确认 `tools/list` 只有 7 个白名单工具。

## Uninstall

```bash
python3 install-tool.py uninstall octocode -p <path>
python3 install-tool.py -u octocode -p <path>
```

卸载只移除 tool pack 文件，不删除 `gh` 登录、全局 Octocode 凭据或项目 `.tmp/agentwork/octocode/` 运行态目录。
