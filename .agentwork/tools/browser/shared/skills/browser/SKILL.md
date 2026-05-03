---
name: browser
description: Browser automation workflow for agentwork's browser-run wrapper; use for web navigation, form interactions, screenshots, PDFs, downloads, snapshots, and project-local browser artifacts.
---

# browser（浏览器自动化）

> 同步来源：`vercel-labs/agent-browser/skills/agent-browser/SKILL.md`。
>
> 命令能力以上游 references 和执行环境中的 `agent-browser --help` 为准；本文件只固化 agentwork 的默认入口、产物目录和保守边界。
>
> 优化策略：保持上游核心流程与用法，但优先收敛到本仓库的 `.tmp/browser`、`browser-run.sh` 和“分步执行”工作流；涉及用户目录持久化或实验特性时，默认保持保守。

## Capability Policy

- 本技能不维护本机版本号；排查能力差异时先读取 `agent-browser --help`。
- 默认工作流包含 CDP 接入、项目内状态文件、下载、截图、PDF、trace、diff、auth 与键盘输入等常用能力。
- 用户目录持久化、native engine、Lightpanda engine、项目外配置文件不纳入默认工作流；使用前先确认项目需求和环境支持。
- 升级 `agent-browser` 后，先复核 CLI 能力，再把稳定的新用法收敛回本技能。

## Workflow Convergence

- 统一入口：优先使用 `.shared/skills/browser/scripts/browser-run.sh`，而不是直接调用 `agent-browser`
- 分步执行：不采用上游文档里的 `&&` 链式调用；每一步单独执行，便于读取 `snapshot` 输出，也符合当前终端工作流
- 项目内持久化优先：状态、截图、录像、PDF、trace、下载等产物默认落在 `.tmp/browser`
- 浏览器状态优先使用项目内 `state save` + `--state`；`auth vault` 可按需使用，但默认仍不依赖会写入用户目录的 `--session-name`
- 涉及真实提交、删除、支付、发布等有副作用操作时，先停在最终点击前，向用户确认

## Tool Priority

- 默认优先使用 `cdp` 工具执行浏览器自动化。
- 仅在 `cdp` 不可用或能力不覆盖时，才回退到 `playwright`。
- 发生回退时，需先说明原因再执行。

## 临时产物目录约定（本仓库补充）

为避免产物随机落在 `.agent/tmp`、`~/.agent-browser` 或系统 `/tmp`，本仓库采用统一目录约定：

- 根目录：`.tmp/browser`
- 统一入口：`.shared/skills/browser/scripts/browser-run.sh`
- 默认下载目录：`.tmp/browser/downloads`
- 临时测试默认优先 CDP：当 `BROWSER_CDP_TARGET=9222` 时，会自动从 `127.0.0.1:9222/json/version` 解析 websocket 地址后执行
- CDP 不可用时自动回退本地模式
- `screenshot`、`record start`、`state save`、`pdf`、`trace stop` 在未显式传路径时，会自动写入 `.tmp/browser`

```bash
# 查看当前目录映射
.shared/skills/browser/scripts/browser-run.sh paths

# 先确认当前页面，再决定是否 open
.shared/skills/browser/scripts/browser-run.sh tab list
.shared/skills/browser/scripts/browser-run.sh get url
.shared/skills/browser/scripts/browser-run.sh snapshot -i
.shared/skills/browser/scripts/browser-run.sh screenshot
```

可选参数：

- `BROWSER_TMP_ROOT`：覆盖根目录（例：`BROWSER_TMP_ROOT=.tmp/browser-login`）
- `BROWSER_CDP_TARGET`：覆盖默认 CDP 端口/地址（默认 `9222`）
- `BROWSER_CDP_PREFER=0`：关闭“优先 CDP”策略

> 默认将 browser 产物收敛到 `.tmp/browser`；如需场景隔离，使用 `BROWSER_TMP_ROOT` 指定目录。
>
> 下文若出现 `agent-browser ...` 原生命令示例，在本仓库执行时都等价替换为 `browser-run.sh` 入口。

## CDP Mode（高频易错，先看这里）

> 参考：<https://agent-browser.dev/cdp-mode>

调用 browser skill 时，优先按下面流程判断如何接入 CDP：

1. **本地 Chrome + 已知端口**：先 `connect` 一次，后续命令不再重复写 `--cdp`
2. **本地 Chrome + 不知道端口**：优先使用 `--auto-connect`
3. **远端浏览器服务**：每条命令显式传 `--cdp "<ws/wss-url>"`

### 方式 A：先连接一次（推荐，多步任务最省心）

```bash
# 先启动带远程调试的 Chrome（示例端口 9222）
google-chrome --remote-debugging-port=9222

# 建立 CDP 连接（一次即可）
agent-browser connect 9222

# 后续命令可直接执行，不必反复加 --cdp
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e2
agent-browser close
```

### 方式 B：每条命令带 `--cdp`

```bash
agent-browser --cdp 9222 snapshot -i
agent-browser --cdp 9222 open https://example.com
```

### 方式 C：自动发现 Chrome（支持时可用）

是否支持 `--auto-connect` 以 `agent-browser --help` 为准；不支持时回退到显式 `connect <port>` 或 `--cdp <port>`。

```bash
agent-browser --auto-connect open https://example.com
agent-browser --auto-connect snapshot -i

# 或使用环境变量（当前 shell 生效）
AGENT_BROWSER_AUTO_CONNECT=1 agent-browser snapshot -i
```

多浏览器并存时，若自动发现结果不符合预期，再回退到显式 `connect <port>` 或 `--cdp <port>`。

### 远端 / 云浏览器（WebSocket URL）

```bash
agent-browser --cdp "wss://browser-service.example/cdp?token=..." snapshot -i
agent-browser --cdp "ws://localhost:9222/devtools/browser/abc123" open https://example.com
```

`--cdp` 支持两种入参：

- 端口号（如 `9222`，等价于连 `http://localhost:{port}`）
- 完整 WebSocket URL（如 `ws://...` / `wss://...`）

### 常见问题速查

- **忘记加 `--cdp` 导致跑到新浏览器**：改为先执行一次 `agent-browser connect <port>`。
- **Chrome 144+ 端口是动态的**：优先用 `--auto-connect`，不稳定时再退回显式端口。
- **连接失败**：先确认目标浏览器已启用 remote debugging，再重试。
- **命令异常退出后再次启动报 socket/daemon 错误**：先结束残留 `agent-browser` daemon，再重试。

## Core Workflow

所有浏览器自动化优先遵循以下流程：

- 当前工作流不做 `&&` 链式调用；每步单独执行，必要时读取中间输出后再继续

1. **Confirm Context**：先 `agent-browser tab list` + `agent-browser get url`
2. **Navigate (If Needed)**：仅在目标页面不一致时执行 `agent-browser open <url>` 或切 tab
3. **Snapshot**：`agent-browser snapshot -i`（获取 `@e1`、`@e2` 等引用）
4. **Interact**：优先使用 `@ref` 做 click/fill/select
5. **Re-snapshot**：页面跳转或 DOM 变化后重新 `snapshot -i`

```bash
agent-browser tab list
agent-browser get url
# 需要跳转时才 open
# agent-browser open https://example.com/form
agent-browser snapshot -i
agent-browser fill @e1 "user@example.com"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i
```

## Essential Commands

仅保留高频命令，完整参数请看 references：

```bash
# Navigation
agent-browser open <url>
agent-browser close

# Snapshot
agent-browser snapshot -i
agent-browser snapshot -i -C
agent-browser snapshot -s "#selector"

# Interaction
agent-browser click @e1
agent-browser fill @e2 "text"
agent-browser type @e2 "text"
agent-browser select @e1 "option"
agent-browser press Enter
agent-browser keyboard type "text"
agent-browser keyboard inserttext "text"

# Wait
agent-browser wait @e1
agent-browser wait --load networkidle
agent-browser wait --url "**/page"

# Capture
agent-browser screenshot --full
agent-browser screenshot --annotate
agent-browser pdf output.pdf

# Diff
agent-browser diff snapshot
agent-browser diff screenshot --baseline before.png
```

## Common Patterns

### Form Submission

```bash
agent-browser open https://example.com/signup
agent-browser snapshot -i
agent-browser fill @e1 "Jane Doe"
agent-browser fill @e2 "jane@example.com"
agent-browser click @e5
agent-browser wait --load networkidle
```

### Authentication with State Persistence

```bash
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "$USERNAME"
agent-browser fill @e2 "$PASSWORD"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save .tmp/browser/auth-state.json

# 新会话复用时，在浏览器启动时带上 --state
agent-browser --state .tmp/browser/auth-state.json open https://app.example.com/dashboard
```

默认工作流以“启动浏览器时显式传 `--state`”为准；不要依赖 `state load` 在已运行浏览器里热加载。若确需使用 `state load`，先核对 `agent-browser --help` 与实际行为。

### Authentication with Auth Vault（按需启用）

```bash
# 推荐从 stdin 读密码，避免进入 shell history
echo "pass" | agent-browser auth save github --url https://github.com/login --username user --password-stdin
agent-browser auth login github
agent-browser auth list
```

`auth vault` 适合跨会话复用登录信息，但默认会写入用户目录。只有在用户明确接受该持久化方式时才使用；否则继续优先项目内 `state save`。

### Parallel Sessions

```bash
agent-browser --session site1 open https://site-a.com
agent-browser --session site2 open https://site-b.com
agent-browser session list
```

### Verification and Extraction

需要验证页面变化时，优先使用 `diff`；需要留证据时再补截图或文本导出：

```bash
agent-browser snapshot -i
# 执行动作后
agent-browser diff snapshot
agent-browser screenshot .tmp/browser/after.png
```

页面比对跨环境或跨 URL 时：

```bash
agent-browser diff url https://staging.example.com https://prod.example.com --wait-until networkidle
agent-browser diff screenshot --baseline .tmp/browser/before.png --output .tmp/browser/diff.png
```

若确实需要更强的结构化比对，优先导出文本、HTML 或截图到 `.tmp/browser`，再在仓库内做后续对照。

### Contenteditable / Editor 输入

对于 Lexical、ProseMirror、CodeMirror、Monaco 等编辑器，优先使用 `keyboard`：

```bash
agent-browser click "[contenteditable]"
agent-browser keyboard type "# Title"
agent-browser press Enter
agent-browser keyboard inserttext "paragraph"
```

### Project-Local Persistence（默认方案）

- 上游新增的 `auth vault` 更适合跨项目长期凭据复用，但默认会引入用户目录级持久化，不作为本仓库默认方案
- 上游 `--session-name` 自动持久化同样不作为默认流程；本仓库优先显式 `--session` 隔离会话、显式 `state save` 持久化状态
- 这样能把状态文件留在项目内，便于审计、清理和会话复现

### Security Guardrails（敏感任务时启用）

- 涉及真实站点、生产环境或高风险动作时，优先考虑 `--allowed-domains`、`--action-policy`、`--confirm-actions`、`--confirm-interactive`
- 需要隔离页面输出与工具输出时，可加 `--content-boundaries`；担心页面文本过长时，可加 `--max-output`
- 默认不把这些限制写死到包装脚本，避免影响普通调试；但在需要保护边界的任务里应主动加上

## Ref Lifecycle (Important)

`@e*` 引用会在页面变化后失效。以下场景后必须重新 `snapshot -i`：

- 点击导致跳转
- 表单提交
- 动态内容加载（下拉、弹窗、异步渲染）

## Semantic Locators (Alternative to Refs)

当 refs 不可用或不稳定时，使用语义定位：

```bash
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find role button click --name "Submit"
```

## Deep-Dive Documentation

- commands：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/references/commands.md>
- snapshot-refs：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/references/snapshot-refs.md>
- session-management：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/references/session-management.md>
- authentication：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/references/authentication.md>
- security：<https://agent-browser.dev/security>
- video-recording：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/references/video-recording.md>
- proxy-support：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/references/proxy-support.md>
- cdp-mode：<https://agent-browser.dev/cdp-mode>

## Ready-to-Use Templates

- form-automation：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/templates/form-automation.sh>
- authenticated-session：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/templates/authenticated-session.sh>
- capture-workflow：<https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/templates/capture-workflow.sh>
