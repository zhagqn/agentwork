# Arch Tool Overview

`/arch` 现在维护的是一个 source-first 静态架构站，而不是运行时布局器。

## What stays in source

- `catalog.json`：站点、版本、分组、顺序和交叉引用
- `index.md`：面向阅读的说明文档
- `diagram.mmd`：文本图源
- `diagram.svg`：稳定展示产物

## What the renderer does

1. 校验 `catalog.json`
2. 校验 item 目录是否具备 Markdown、文本图源和 SVG
3. 生成根导航页、item 页面和共享 CSS

## Notes

- 页面路径由 `content/<version>/<item>/` 推导
- 默认不引入前端脚本
- 文本图源到 SVG 的转换由外部流程负责
