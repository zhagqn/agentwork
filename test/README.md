# agentwork test harness

测试脚本放在 `test/`，临时测试项目与结果输出放在 `.tmp/`。

## 主入口
- `python3 test/run.py`
- 可指定 provider：`python3 test/run.py --provider codex`
- 可指定 provider 模型和推理强度：`python3 test/run.py --provider codex --model gpt-5.4 --reasoning-effort xhigh`
- Codex fast mode 可用 `--fast` 快捷启用：`python3 test/run.py --provider codex --model gpt-5.4 --reasoning-effort xhigh --fast`
- 失败后可接力：`python3 test/run.py --resume .tmp/integrated-harness/runs/{run-id}`
- 也可只重跑单个阶段：`python3 test/run.py --resume {run-id} --stage session`
- 每次运行写入独立目录：`.tmp/integrated-harness/runs/{run-id}/`

## 测试标准
- 单次 integrated run 覆盖当前主要测试标准，不再要求维护者串多个小 case。
- 当次 run 只创建一个临时目标项目：`.tmp/integrated-harness/runs/{run-id}/project/`。
- `install-bootstrap.py` 和 `install-tool.py` 从当前 source repo 执行，并且必须真正安装到这个临时项目；目标项目不应泄漏 source install 脚本。
- `brain`、`plan`、`exec`、`review` 四个命令都在同一个已安装项目中继续运行，验证目标项目内的真实工作流体验。
- 独立命令场景使用一个最小 Node.js HTTP JSON probe 小轮子，覆盖 CLI 设计、HTTP JSON 读取、字段校验、成功 / 失败路径验证和使用文档，且不引入 npm 依赖，只依赖 Node.js 内置能力和本地 localhost fixture server。
- 独立命令场景允许 `$exec` 最多连续推进两轮；若第一轮只完成计划的一部分，第二轮继续同一个 plan，模拟真实项目里分批执行直到本轮验收闭环。
- HTTP fixture server 必须支持由 harness 指定端口，兼容 `--port <port>` 或 `PORT=<port>`；`GET /ok` 必须返回根字段 `status: "ok"` 和 `version`，`GET /bad-contract` 必须无法通过同一契约。
- integrated run 包含一个简化 Mini Dinner Flow 迭代场景：`apps/api`、`apps/admin`、`apps/h5`、`packages/shared`，参考 NestJS 分层、Drizzle/SQLite 数据建模和前后端共享类型方向，但只实现测试所需最小骨架。
- Turborepo 场景必须通过 session mode 分次推进 `$session brain`、`$session load` + `$session exec`、`$session load` + `$session review`，每一步都是独立 provider 调用，并最终用 session 标准检查器确认没有漂移。
- Bootstrap contract 检查 subagent pattern 是否安装到目标项目，并确认 `/exec`、`/review` 与 session workflow 的 subagent 引用入口和核心章节没有漂移。
- Harness 不判断业务实现细节；独立命令场景只检查 HTTP probe 的 CLI、文档、fixture server 和可运行验收；Turborepo 场景只检查共享类型、后端 menu/orders 边界、README、session 不漂移和文件范围受控。

## 当前脚本
- `run.py`：集成测试入口，负责新建 run、resume、阶段接力和报告刷新。
- `stages/`：按 install、independent、session 拆分的阶段入口。
- `harness.py`：共享 harness 能力、provider 调用、日志、断言和底层 stage 实现。
- `check_bootstrap_contract.py`：bootstrap 安装契约检查器，由 integrated run 调用。
- `check_session_standard.py`：session 标准结构检查器，由 integrated run 调用；`--strict-flow` 用于完整 session flow，在该模式下模板中标注“可选”的计划摘要、当前批次工作集和产出批次小节也必须保留。

## 场景资产
- `test/flow/flow.json`：定义 integrated harness 中 provider 调用顺序、command input 文件、schema key 和 timeout。
- `test/flow/independent-*.txt`：独立命令输入，模拟 `$brain`、`$plan`、`$exec`、`$review`。
- `test/flow/turborepo-session-*.txt`：session mode 命令输入，模拟 `$session brain`、`$session load`、`$session exec`、`$session review`。
- 场景输入不重复提示 agent 阅读 AGENTS、commands 或 templates；约束加载应由被测命令入口和 agent 自身完成。
- `run.py` 只负责调度与接力；测试意图和命令输入不直接写在脚本主体中。

## 输出目录
- `.tmp/integrated-harness/runs/{run-id}/project/`：本次 run 的唯一临时目标项目。
- `.tmp/integrated-harness/runs/{run-id}/results/summary.md`：最终人读报告。
- `.tmp/integrated-harness/runs/{run-id}/results/summary.json`：最终机器可读结果。
- `.tmp/integrated-harness/runs/{run-id}/results/latest.md`：运行中持续刷新的阶段进度；中断时优先看这个文件。
- `.tmp/integrated-harness/runs/{run-id}/results/latest.json`：运行中持续刷新的机器可读状态。
- `.tmp/integrated-harness/runs/{run-id}/results/live.md`：运行中的实时关键日志，记录 harness heartbeat、provider 关键对话行和结构化输出。
- `.tmp/integrated-harness/runs/{run-id}/results/logs/{stage}/`：原始 stdout、stderr 和 meta 日志，按阶段分组，只在调试时查看。
- `summary.*` 和 `latest.*` 会记录 provider、model、reasoning_effort、service_tier；需要确认真实命令参数时查看对应阶段的 `.meta.json`。
- `summary.*` 和 `latest.*` 中的项目路径优先使用仓库相对路径；需要真实执行路径时查看对应阶段的 `.meta.json`。

## 边界
- 当前测试验证 workflow 工件契约、安装结果、真实 provider 执行结果和 drift 检查。
- 当前测试不证明 provider 原生 subagent 是否真的启动；只验证 subagent 共享规范的安装、入口引用和核心章节。
- 当前测试不做完整 Mini Dinner Flow 业务实现；Turborepo 场景只保留足以验证后端分层、共享类型和前后端 workspace 迭代的最小结构。
- 当前测试不要求完整 NestJS / Drizzle / SQLite 可运行应用，避免把脚手架细节误判为 workflow 标准。
