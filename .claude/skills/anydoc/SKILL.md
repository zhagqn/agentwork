---
name: anydoc
description: 按需将 Word、PowerPoint、Excel、OpenDocument、RTF、EPUB、CSV 和 PDF 转为 Markdown，供 agent 分析和归档。
---
# anydoc 文档解析

这是 agentwork 的默认文档输入能力。仅当任务需要读取二进制办公文件时使用；纯文本、代码和已有 Markdown 不需要经过 anydoc。

## 项目级延迟安装

先检查项目是否已有依赖：

```bash
npx --no-install @firecrawl/anydoc --help
```

如果缺失且项目允许安装，在项目根目录执行：

```bash
npm install --save-dev @firecrawl/anydoc@0.2.4
```

禁止全局安装。安装前应遵守项目的联网、依赖修改和锁文件策略；离线环境使用内部 npm 镜像或已缓存的包。

## 转换与归档

```bash
mkdir -p .tmp/anydoc
npx --no-install @firecrawl/anydoc INPUT -o .tmp/anydoc/OUTPUT.md
```

保留原文件；Markdown 和抽取出的 JSON 元数据写入 `.tmp/anydoc/` 或项目约定的归档目录。记录 anydoc 版本、输入路径、格式和失败原因。转换结果用于分析和索引，不替代原始文件，也不保证版式保真。

## OCR 与失败边界

默认禁止 hosted OCR。扫描或图片型 PDF 转换失败时记录 `NeedsOcr`，优先让当前 agent 使用已有的视觉能力读取 PDF 页面或页面图像，并继续当前分析任务；不需要为此安装 OCR 服务。只有当前环境无法提供视觉输入、文档规模超出可处理范围，或用户明确授权外部 OCR 时，才转交受信任的 OCR 服务。对 `Encrypted`、`Unsupported`、`NeedsOcr` 等文件单独登记并继续处理其他输入，不绕过密码或安全策略。
