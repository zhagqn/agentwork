# agentwork Workflow Architecture

本目录用于沉淀当前 `agentwork` 工作流架构的正式图。

## 文件约定
- `diagram.arch.json`：根图事实源
- `index.html`：根图渲染结果
- `nodes/<slug>/diagram.arch.json`：子图事实源
- `nodes/<slug>/index.html`：子图渲染结果

## 当前图
- 根图：`diagram.arch.json`
- 子图：`nodes/workflow-core/diagram.arch.json`

## 渲染方式
```bash
python3 .shared/scripts/architecture-render.py docs/architecture --recursive
```
