---
name: anydoc
description: 按需将 Word、PowerPoint、Excel、OpenDocument、RTF、EPUB、CSV 和 PDF 转为 Markdown，供 agent 分析和归档。
---
# anydoc 文档解析

这是 agentwork 的默认文档输入能力。仅当任务需要读取二进制办公文件时使用；纯文本、代码和已有 Markdown 不需要经过 anydoc。

## 项目级延迟安装

运行需要 Node.js >=20。先检查项目是否已有 CLI：

```bash
npx --no-install @firecrawl/anydoc --help
```

如果缺失且项目允许安装，遵循已有包管理器和锁文件约定；使用 npm 的项目在根目录执行：

```bash
npm install --save-dev @firecrawl/anydoc@0.2.4
```

禁止全局安装。非 Node 项目先确定项目内的依赖目录，不直接改变项目技术栈。安装前遵守项目联网策略；离线环境使用内部 npm 镜像或已缓存的包。

`--help` 不加载原生 binding，成功不代表转换可用。首次使用时先转换一个小型本地样例并检查输出。

## 转换与归档

```bash
mkdir -p .tmp/anydoc
npx --no-install @firecrawl/anydoc INPUT -o .tmp/anydoc/OUTPUT.md
```

保留原文件；CLI 默认只输出 Markdown，写入 `.tmp/anydoc/` 或项目约定的归档目录；需要元数据时再另行提取。记录 anydoc 版本、输入路径、格式和失败原因。转换结果用于分析和索引，不替代原始文件，也不保证版式保真。

## OCR 与失败边界

默认禁止 hosted OCR。扫描或图片型 PDF 转换失败时记录 `needsOcr`，优先使用当前 agent 已有的视觉能力读取页面或页面图像。视觉不可用或文档过大时，说明限制并考虑分批处理，不自动转交外部服务。只有用户明确授权将当前资料发送给指定外部 OCR 服务后，才可转交；`--ocr hosted` 会上传文档。失败文件记录实际错误并继续处理其他输入，不绕过密码或安全策略。
