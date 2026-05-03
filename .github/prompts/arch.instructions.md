# Arch Tool Instructions

当任务需要生成或调整架构图时：
- 先阅读 `.shared/commands/arch.md`
- 默认优先维护 `catalog.json`、根导航页和 `diagrams/<slug>/` 下的图表 source
- 已有 `catalog.json` 时，新图按 `parent_id` / `order` / standalone 规则合并进导航
- 新图优先使用 `layout.mode=auto`，通过 `groups` / `rank` / 连线拓扑表达布局
- 架构 / 流程主路径优先使用 `overview`、`topology`、`flow`；其他 Mermaid 类型仅作为参考图
- 调整后优先运行 renderer `--recursive --check`，必要时读取 `.shared/templates/arch/references/layout-best-practices.md` 和 `portal-workflow.md`
- 通过 `.shared/scripts/arch-render.py docs/architecture --recursive` 生成静态 HTML
- 正式产物默认放 `docs/architecture/`，临时草稿默认放 `.tmp/architecture/`
- 不引入 server、live reload、搜索、权限或托管预览
