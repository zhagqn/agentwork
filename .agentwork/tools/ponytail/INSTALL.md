# Install Ponytail Tool

## What gets installed
- `.shared/tools/ponytail.md`（引用型参考文档，不含上游源码）

## Install
```bash
python3 install-tool.py install ponytail -p <path>
python3 install-tool.py -i ponytail -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall ponytail -p <path>
python3 install-tool.py -u ponytail -p <path>
```

## After install
- 本 tool pack 只物化参考文档；ponytail 本体需按 `.shared/tools/ponytail.md` 在各平台用官方安装器接入
- Claude Code：两条独立消息 `/plugin marketplace add DietrichGebert/ponytail` → `/plugin install ponytail@ponytail`
- Codex：`codex plugin marketplace add DietrichGebert/ponytail` + `codex plugin add ponytail@ponytail`，随后在 `/hooks` 中信任其 lifecycle hook
- 前置：`node` 需在非交互 shell 的 PATH 上
- 验证：新会话中执行 `/ponytail`（Codex 为 `@ponytail`）应报告当前档位
- 默认使用 `full` 档；只有实际出现与 `coding-style.md` 叠加的提示噪音时再降为 `lite` 或二选一
- 上游为高速迭代项目；安装命令若失效，以官方仓库 README 为准
