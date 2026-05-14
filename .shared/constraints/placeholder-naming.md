# 文档占位符命名规范

用于统一命令文档中的参数占位符命名，降低跨助手协作时的歧义与维护成本。

## 命名总则

- 语义优先：占位符应直接表达“数据类型 + 业务语义”，避免过短泛名（如 `<id>`）。
- 域前缀优先：跨域场景加前缀（如 `session-`、`figma-`），减少重名冲突。
- 可选参数用 `[]`，必填参数用 `<>`。
- 同一语义全仓统一命名，不在不同文档里换同义词。

## 标准命名表

| 占位符 | 含义 | 示例 |
| --- | --- | --- |
| `<session-desc>` | 新建 session 的简述文本 | `修复欢迎页焦点问题` |
| `<brain-topic>` | 头脑风暴主题 | `用户登录功能` |
| `<session-id>` | session 文件名（不含 `.md`） | `20260120-1030-xxx` |
| `<session-ref>` | session 标识（可为 `<session-id>` 或文件路径） | `20260120-1030-xxx` / `.shared/session/20260120-1030-xxx.md` |
| `[session-ref]` | 可选 session 标识；省略时使用当前 session | `20260120-1030-xxx` / `.shared/session/20260120-1030-xxx.md` |
| `[plan-source]` | plan 命令的输入来源 / 引用对象（可为 session、brain note、任意文本路径） | `.shared/session/20260120-1030-xxx.md` / `.tmp/agentwork/brain/foo.md` |
| `[exec-source]` | exec 命令的输入来源 / 引用对象（通常为 session 或 plan 文件） | `.shared/session/20260120-1030-xxx.md` / `.tmp/agentwork/plan/foo.md` |
| `[review-source]` | review 命令的审查来源 / 引用对象（通常为 session 或 plan 文件） | `.shared/session/20260120-1030-xxx.md` / `.tmp/agentwork/plan/foo.md` |
| `<commit-hash>` | Git 提交 hash（通常为短 hash） | `9f3c2ab` |
| `<commit-subject>` | Git 提交标题（单行 subject） | `修复登录页焦点回退` |
| `<lsp-location>` | LSP 位置（`path:line:column`，1-based） | `src/main.ts:18:7` |
| `[arch-root]` | 架构图工具的目标根目录 | `docs/architecture` / `.tmp/architecture` |
| `<arch-task-desc>` | 架构站工具的口语化任务描述 | `生成当前版本总览页并补 payment-runtime 文档` |
| `[diagram-ref]` | 架构站根目录、`catalog.json`、item 目录或 item source 路径 | `docs/architecture` / `docs/architecture/catalog.json` / `docs/architecture/content/current/system-overview` |

> 维护规则：仅登记仓库已使用的占位符；命令或模板新增占位符时同步更新本表。

## 反例（避免使用）

- `<id>`、`<desc>`、`<topic>`（语义过宽）
- `<task-or-sql>`（与 query 语义重复，不利于统一）
- `[node-or-url]`（仅在 Figma 场景出现，建议显式为 `[figma-target]`）
