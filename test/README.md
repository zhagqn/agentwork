# agentwork test harness

测试脚本放在 `test/`，临时测试项目与结果输出放在 `.tmp/`。

## 设计原则
- bootstrap 基础文件、block、占位符泄漏、Codex skill frontmatter 这类结构约束：直接脚本硬校验
- project 轻量索引与本地内容保留：直接脚本硬校验
- tools 的安装/卸载路径与 bootstrap 隔离：直接脚本硬校验
- 不做细粒度评分；结果只看 pass / fail / skipped
- `test/` 只放测试脚本；测试项目与结果统一落到 `.tmp/`
- tools 的真实可用性仍保留人工审查入口，不做“看起来通过但实际信号弱”的自动评分
- 真实 CLI harness 兼容 provider 返回绝对路径/相对路径两种文件列表格式，并对容量类瞬时失败做轻量重试
- summary 会附带时间维度：整体开始/结束/总耗时，以及每个 case 的开始/结束/耗时

## 当前脚本
- `check_bootstrap_contract.py`：检查 bootstrap 产物结构、project/session block、本地内容保留、Codex skill frontmatter
- `run_deterministic.py`：bootstrap、轻量 project 索引、tool 安装/卸载、bootstrap-tool 隔离，以及 arch render smoke 的硬校验
- `run_real_cli.py`：真实调用 Codex / Claude CLI 的 harness
- `cases/*.json`：promptfoo 风格的轻量断言用例（只保留 deterministic assertions + 人工审查清单）

## 当前 case
- `session_planning`：session 模式，创建最小 session 快照
- `brain_readme_intro`：standalone `/brain`，生成方案收敛笔记
- `plan_readme_intro`：standalone `/plan`，基于 brain note 生成执行计划
- `exec_readme_intro`：standalone `/exec`，按计划落地最小 README 改动并回写 plan
- `exec_ralph_readme_intro`：standalone `/exec --ralph`，验证 Ralph 工件、完成态 progress 与 subagent-first 记录
- `review_readme_intro`：standalone `/review`，对 plan 与工作区事实生成 review 工件

## 当前边界
- 当前 harness 可以验证 Ralph / subagent-first 的**工件契约与流程记录**
- 当前 harness **不直接证明** provider 在运行中真的启动了原生 subagent，因为现有 CLI 输出面没有稳定暴露可编程的 subagent trace

## 输出目录
- `.tmp/harness/repos/`：临时测试项目
- `.tmp/harness/results/`：deterministic harness 结果
- `.tmp/real-harness/repos/`：真实 CLI 测试仓库
- `.tmp/real-harness/results/`：真实 CLI 测试结果、逐 attempt 日志、逐 case `*.result.json`、可读的 `summary.md`，以及运行中持续刷新的 `summary.latest.json` / `summary.latest.md`
