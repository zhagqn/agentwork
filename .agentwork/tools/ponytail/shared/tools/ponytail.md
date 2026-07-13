# Ponytail Reference

该文件是 ponytail 可选工具的引用型参考文档：只记录官方接入路径，不 vendor 上游源码。

- 上游：<https://github.com/DietrichGebert/ponytail>（MIT）
- 定位：行为级"少写代码"规则注入——在写代码前按分级判断收敛实现（是否需要存在 → 代码库已有 → 标准库 → 平台原生能力 → 已装依赖 → 一行 → 最小实现）；信任边界校验、数据丢失处理、安全、可访问性不受此分级裁剪
- 免责：本文档若与官方仓库最新说明不一致，以官方为准

## 前置条件

- Claude Code / Codex 的 plugin 形态依赖两个轻量 Node.js lifecycle hook，`node` 需在**非交互 shell 的 PATH** 上（Nix/nvm 用户注意）；缺失时 skill 仍可用，只是 always-on 激活静默失效

## Claude Code

分两条独立消息发送：

```text
/plugin marketplace add DietrichGebert/ponytail
```

```text
/plugin install ponytail@ponytail
```

## Codex

```bash
codex plugin marketplace add DietrichGebert/ponytail
codex plugin add ponytail@ponytail
```

安装后运行 `codex`，打开 `/hooks` 审查并信任其两个 lifecycle hook，再开新线程生效。Codex 中命令以 skill 形式用 `@` 触发（如 `@ponytail-review`）。

## 其他平台

Cursor / Copilot / Antigravity 等 instruction-only 平台可复制上游仓库对应 rules 文件（`.cursor/rules/`、`.github/copilot-instructions.md`、`AGENTS.md` 等），只加载 always-on 规则、无命令；完整平台映射见上游 `docs/agent-portability.md`。

## 日常使用

**装完即全自动，无需任何主动调用**：hook 每轮自动注入规则集，agent 写代码时自然受约束，默认 `full` 档即可，不需要折腾配置。

可选命令（不用也不影响核心价值）：

- `/ponytail-review`：审查当前 diff 的过度设计，产出 delete-list
- `/ponytail-audit`：全仓过度设计审计
- `/ponytail [lite | full | ultra | off]`：调整强度或关闭；无参数时报告当前档位

进阶配置（通常不需要动，只在实际感到提示噪音时再看）：`PONYTAIL_DEFAULT_MODE` 或 `~/.config/ponytail/config.json` 设默认档位；`PONYTAIL_SUBAGENT_MATCHER` 限定子代理注入范围。

## 卸载

先运行清理脚本，再执行 host 卸载（顺序不可反，脚本本身是 plugin 文件）：

```bash
node scripts/uninstall.js   # 在 ponytail checkout 内执行，清理 mode flag / config / statusLine
```

然后 Claude Code 内 `/plugin remove ponytail`，或 `codex plugin remove ponytail`。

## 与 agentwork 约束的关系

- 本仓库 `.shared/constraints/coding-style.md` 已含同方向的 YAGNI 类约束；两者叠加通常无害，只有实际感到提示噪音时才需要降档或二选一
- 与 codegraph 组合：ponytail 第 2 级"代码库已有 → 复用"在大仓库里依赖低成本的语义检索，配合 codegraph 效果更好；读写两端同时收敛
- 是否启用属于平台层决策，agentwork 不预装、不默认开启
