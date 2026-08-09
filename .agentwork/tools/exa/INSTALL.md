# Install Exa Tool

## What gets installed

- `.shared/mcp/exa.md`
- `.shared/scripts/exa-mcp.py`
- 项目根 `.env` 中缺失的 `EXA_API_KEY=` 空占位

安装器还会在需要时向项目根 `.gitignore` 追加 `.env`，但不会覆盖或回显已有值。

## Install

```bash
python3 install-tool.py install exa -p <path>
python3 install-tool.py -i exa -p <path>
```

## Configure

只编辑目标项目根 `.env`，在等号右侧填写 key：

```dotenv
EXA_API_KEY=
```

不要把 key 放进命令参数、MCP 配置或对话。检查凭据、Node 和 npx readiness 时使用：

```bash
python3 .shared/scripts/exa-mcp.py --check
```

## Uninstall

```bash
python3 install-tool.py uninstall exa -p <path>
python3 install-tool.py -u exa -p <path>
```

未填写的受管占位会被移除；已填写值会保留并解除 agentwork marker。`.env` 文件和 `.gitignore` 规则不会被删除。

## After install

- 需要 Node.js `>=20.0.0` 和可用的 `npx`
- 按 `.shared/mcp/exa.md` 手动接入当前客户端；Codex 使用项目 `.codex/config.toml`，Claude 使用 local scope
- 默认只暴露 `web_search_exa` 与 `web_fetch_exa`
- 不自动合并任何平台 MCP 私有配置
