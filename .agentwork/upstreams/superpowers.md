# Superpowers Foundation Mapping

本文件定义 `obra/superpowers` 如何作为 agentwork 的上游工作流基座存在，并说明如何在 `.agentwork/*` 中维护升级与映射。

## 本地上游镜像
- 路径：`.tmp/superpowers/`
- 当前已检视版本：`917e5f53b16b115b70a3a355ed5f4993b9f8b73d`（2026-04-06）

## 更新方式
```bash
if [ ! -d .tmp/superpowers/.git ]; then
  git clone --depth=1 https://github.com/obra/superpowers.git .tmp/superpowers
else
  git -C .tmp/superpowers fetch --depth=1 origin main
  git -C .tmp/superpowers reset --hard origin/main
fi
git -C .tmp/superpowers log -1 --oneline
```

## 核心思路
- `.tmp/superpowers/` = 本地上游镜像（source）
- `.shared/*` = 选择性整理后的可同步 workflow contract（output）
- `.agentwork/*` = source 维护、映射、foundation/tools 机制（maintenance）

## 当前映射
| agentwork surface | superpowers upstream | 迁移重点 |
| --- | --- | --- |
| `/brain` | `skills/brainstorming/SKILL.md` | 先看上下文、一次一问、2-3 方案、确认后再落最终态 |
| `/plan` | `skills/writing-plans/SKILL.md` | bite-sized task、边界先行、无占位、验证前置 |
| `/exec` | `skills/executing-plans/SKILL.md` | 执行前先复核、遇 blocker 停止、不猜 |
| `/review` | `skills/requesting-code-review` + `receiving-code-review` | review early、反馈先验证、只沉淀高信号技术结论 |
| `/session` | 上述 4 个 surface 的组合适配 | 作为任务快照外壳，把 brain / plan / exec / review 串起来 |

## 维护流程
1. 按上面的命令刷新 `.tmp/superpowers`
2. 记录最新 upstream commit
3. 对照本文件的映射表做 review
4. 选择性更新 `.shared/commands/*` / `.shared/patterns/*` / `.shared/templates/*`
5. 跑格式 / 引用 / 自检脚本
