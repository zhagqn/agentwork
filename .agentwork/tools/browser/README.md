# Browser Tool Pack

## 类型
- skill
- local tool wrapper (`agent-browser`)

## 内容
- shared browser skill
- browser-run.sh 统一入口脚本
- Codex / Claude / Agent 平台入口

## 何时物化
- 项目需要浏览器自动化、表单交互、截图、抓取、PDF、state save 等能力
- 需要将浏览器产物统一落盘到项目 `.tmp/browser`

## 适配原则
- shared 主定义是 source of truth
- 各 AI 工具只保留入口说明，不复制主流程正文
