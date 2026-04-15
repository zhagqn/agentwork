# /commit

代码提交命令（手动触发）。

## 核心要求
- 仅在用户显式输入 `/commit` 时执行
- 提交前必须先做 diff + 最小验证
- 默认不执行 push，尤其不主动建议 `git push --force`
- 若采用“先业务改动，再 docs(session)”双提交，第二次提交前必须回填业务提交锚点

## Session 锚点检查
- 若提交包含 `.shared/session/*.md`，必须检查“产出物（含提交锚点）”相关条目是否已填写真实 hash
- 若仍是 `提交: -`，且上一批次刚提交了业务改动，必须先回填 `提交: <commit-hash> <commit-subject>`

## 当前项目工件关系
- 若上下文已经在 `.shared/session/*`、`.shared/project/*`、`research/*` 中充分记录，提交信息不需要重复冗长背景
- 默认不提交 `.tmp/*` 临时工件，除非用户明确要求保留证据
