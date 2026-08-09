# Install Research Tool

## What gets installed

- `.shared/skills/research/SKILL.md`
- thin wrappers for Codex / Claude / Cursor

评测用例、provider、二进制、密钥和平台 MCP 配置不会安装到目标项目。

## Install

```bash
python3 install-tool.py install research -p <path>
python3 install-tool.py -i research -p <path>
```

## Uninstall

```bash
python3 install-tool.py uninstall research -p <path>
python3 install-tool.py -u research -p <path>
```

## After install

- 直接描述需要当前事实、跨来源比较、实现证据或社区信号的问题；也可显式使用 `$research 调研 Node.js 当前发布线并引用一手来源`。
- 平台入口会先读取共享定义，再优先选择本地文件、官方资料或 `gh`；不要求用户点名 provider。
- 需要未知公开 Web 发现或已知 URL 批量读取时，单独安装 Exa；跨仓库实现证据确有收益时再安装 experimental Octocode。
- 使用可选 provider 前，按项目约定完成项目级 MCP 接入和 readiness 检查。
