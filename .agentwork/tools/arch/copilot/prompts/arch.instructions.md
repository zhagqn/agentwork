# Arch Tool Instructions

当任务需要生成或调整架构图时：
- 先阅读 `.shared/commands/arch.md`
- 默认优先维护 `catalog.json` 和 `content/<version>/<item>/` 下的 Markdown、文本图源与 SVG
- 页面路径由 `version + id` 推导，不在 catalog 中重复维护派生字段
- 调整后优先运行 renderer `--check`，必要时读取 `.shared/templates/arch/references/layout-best-practices.md` 和 `portal-workflow.md`
- 通过 `.shared/scripts/arch-render.py docs/architecture` 生成静态页面与共享 CSS
- 正式产物默认放 `docs/architecture/`，临时草稿默认放 `.tmp/architecture/`
- 不引入 server、live reload、搜索、权限或托管预览
