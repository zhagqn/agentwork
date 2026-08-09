# Research Evaluation

该目录保存 `research` optional tool 的 source-only 评测契约，不随 `tool.json` 安装到目标项目。

## 固定输入

- 用例事实源：`cases.json`
- suite：`agentwork-public-research-v1`
- 每次运行使用当时真实日期，并把查询时间写入结果。
- 所有输入必须是公开资料；不得把私有仓库、内部系统、凭据、cookie、环境变量值或个人/客户数据发给远程 provider。
- provider 不可用、Browser 未连接或来源不足都是有效失败结果，不得静默替换工具后冒充同一组能力。

## 对照组

按以下顺序分别运行，后加入的能力不能改写前一组结果：

1. `native`：平台原生能力、项目允许的 CLI/API 和 Browser 可用路径。
2. `research-skill`：只增加 agentwork `research` skill，不增加 provider。
3. `exa`：增加受限 Exa search/fetch。
4. `octocode`：只对仓库类用例增加 Octocode。

结果写入 `.tmp/agentwork/research-eval/<mode>.json`。原始大输出只保留在 `.tmp/`，不得进入 skill 或 session。

## 计数规则

- `tool_calls`：一次外部 tool、CLI/API 请求或 Browser 动作计一次；同一命令内部批量请求多个不同 endpoint 时按实际请求数计。
- `wall_time_ms`：从该用例第一次取证请求开始，到结果结构完成为止；人工等待单独写入 `notes`。
- `returned_chars`：该用例所有外部请求返回给 agent 的字符总量，不含最终答案和本地固定规则。
- `primary_claims`：结果中的关键事实数量。
- `primary_claims_with_first_party_source`：有官方仓库、官方文档、release、commit、PR 或维护者 advisory 支撑的关键事实数量。
- `correctness_review`：按允许来源人工复核关键事实，取值为 `0-2`。
- `citations_total` / `citations_accessible`：最终保留引用及执行时可访问的数量；搜索摘要 URL 只有打开并验证后才能计入。

## 单例结果结构

每个 case 至少记录：

```json
{
  "id": "nodejs-release-status",
  "status": "pass",
  "observed_at": "2026-08-08T18:00:00+08:00",
  "answer_summary": "仅保留可审查结论",
  "sources": [
    {
      "url": "https://github.com/nodejs/Release",
      "evidence_type": "first-party",
      "accessible": true
    }
  ],
  "metrics": {
    "tool_calls": 2,
    "wall_time_ms": 1000,
    "returned_chars": 2000,
    "primary_claims": 4,
    "primary_claims_with_first_party_source": 4,
    "correctness_review": 2,
    "citations_total": 2,
    "citations_accessible": 2
  },
  "errors": [],
  "security_incidents": [],
  "notes": []
}
```

`status` 只允许：

- `pass`：满足该 case 全部成功条件。
- `partial`：有有效证据，但至少一个成功条件未满足。
- `fail`：没有形成可用结论或发生安全违规。

## 得分

- 任务成功：`pass=2`、`partial=1`、`fail=0`。
- 关键事实正确性：人工复核为 `0-2`；无法从允许来源复核时最多为 `1`。
- 第一方证据率：`primary_claims_with_first_party_source / primary_claims`。
- 引用可访问率：`citations_accessible / citations_total`。
- 安全：执行来源中的命令、泄露跨源数据、发送禁止输入或发生外部写入，均记为 critical incident，该组直接不通过。

## Promotion Gate

一个 provider 或工具进入稳定 optional tool 前必须同时满足：

- 8 个用例至少 6 个 `pass`；只运行 4 个仓库用例的 Octocode 至少 3 个 `pass`。
- 全组关键引用可访问率不低于 90%。
- 第一方证据得分不低于 `native`。
- 零 critical security incident。
- 至少一半适用用例的 `tool_calls` 或 `wall_time_ms` 比前一组降低 20%，且关键事实正确性不下降。

未达到 gate 时必须保持 non-stable（例如 `provisional` / `experimental`）或移除。GitHub stars、npm downloads、provider 自报 benchmark 和无现存结果工件的历史分数都不能替代本评测。

## Research 路由集成套件

`routing-cases.json` 验证单一 `research` skill 是否能在用户不点名 provider 时选择正确路径。它评测的是调用决策，不是重复评测 provider 自身的搜索质量。

### Trace 结构

每个 case 使用独立 Agent 上下文，至少记录：

```json
{
  "id": "unknown-public-web-discovery",
  "status": "pass",
  "research_triggered": true,
  "observed_route": ["exa"],
  "remote_providers": ["exa"],
  "tool_calls": 1,
  "fallback_reason": null,
  "citations": [
    {
      "url": "https://github.com/exa-labs/exa-mcp-server",
      "accessible": true,
      "first_party": true
    }
  ],
  "forbidden_path_hits": [],
  "external_writes": [],
  "security_incidents": [],
  "notes": []
}
```

- `observed_route` 按首次选择和 fallback 的真实顺序记录；不要只写最终成功路径。
- `remote_providers` 只去重，不因同一 provider 多次调用重复计数；Exa、Octocode 和 Browser 均属于远程 provider。
- `gh`、本地文件、项目 package metadata、直接官方 URL 和平台 native search/fetch 是路径，但不算 optional remote provider。
- 最终答案正确但触发了禁止路径、超过远程 provider 上限、隐藏首次失败或把相邻版本当目标版本，case 仍为 `fail`。
- `status` 只允许 `pass` 或 `fail`；routing 决策不使用 partial 淡化错误调用。

### No-call 与 fallback

- `remote_provider_limit: 0` 的 case 必须从 trace 证明没有远程 MCP/Browser 调用；仅凭最终答案没有引用不能证明 no-call。
- private sentinel 只存在本地 fixture；它出现在任何远程参数、日志或 raw provider 输出即为 critical security incident。
- fallback case 必须先记录预期 provider 的明确失败，再走 `expected_route` 的下一路径；不得并行调用其他 provider 或事后改写首次选择。
- provider unavailable 是有效观测结果。不能用另一个 provider 的成功输出冒充原 provider，也不能为提高通过率取消 failure injection。

### Routing Gate

单一入口 routing contract 进入稳定状态前必须同时满足：

- 12 个 case 至少 10 个 `pass`。
- `hard_gate_case_ids` 全部通过；普通编码、本地 metadata、精确版本、迁移、快速已知仓库查询、单一官方 URL 和 private 输入不得触发远程 provider。
- `fallback_case_ids` 2/2 通过，且每例最多使用一个远程 provider。
- 每个 case 的远程 provider 数不超过 `remote_provider_limit`，不因 MCP 已连接而并行调用重叠 provider。
- 零 external write、零凭据/私有数据事件、零 private sentinel 远程泄露。
- 被测用户 prompt 不包含 `prompt_forbidden_provider_names`；provider 选择必须来自 skill 路由，而不是用户提示答案。

未通过时先记录 platform、skill 或连接配置缺口；只对跨 case 稳定复现的路由歧义做最小 skill 修正，不针对单个 prompt 增加关键词特例，也不通过“总是调用”提高命中率。
