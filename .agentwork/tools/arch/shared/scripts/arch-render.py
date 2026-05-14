#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from string import Template


SOURCE_LABELS = {
    "mmd": "Mermaid 源",
    "puml": "PlantUML 源",
    "dot": "Graphviz DOT 源",
}

KNOWN_ITEM_FILENAMES = {"index.md", "index.html", "diagram.svg"} | {f"diagram.{ext}" for ext in SOURCE_LABELS}
WIDE_DIAGRAM_THRESHOLD = 1600.0
SVG_OPEN_TAG_PATTERN = re.compile(r"<svg\b([^>]*)>", re.IGNORECASE)
SVG_VIEWBOX_PATTERN = re.compile(r'\bviewBox="([^"]+)"')
SVG_WIDTH_PATTERN = re.compile(r'\bwidth="([0-9.]+)(?:px)?"')
SVG_STYLE_MAX_WIDTH_PATTERN = re.compile(r"max-width:\s*([0-9.]+)px")

CSS_CONTENT = """
:root {
  --bg: #f6f1e8;
  --surface: rgba(255, 252, 246, 0.96);
  --surface-strong: #fffdfa;
  --line: rgba(204, 184, 156, 0.9);
  --line-strong: rgba(163, 139, 112, 0.92);
  --ink: #1f2c2d;
  --muted: #5f6c6d;
  --accent: #0f766e;
  --accent-strong: #115e59;
  --accent-soft: rgba(15, 118, 110, 0.1);
  --warm: #aa6232;
  --shadow: 0 20px 44px rgba(62, 53, 42, 0.08);
  --radius-lg: 24px;
  --radius-md: 16px;
  --radius-sm: 10px;
  --sans: "Avenir Next", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --serif: "Iowan Old Style", "Palatino Linotype", "Songti SC", Georgia, serif;
}

* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  min-height: 100%;
}

body {
  background:
    radial-gradient(circle at top left, rgba(241, 223, 199, 0.45), transparent 26%),
    linear-gradient(180deg, #faf5ec 0%, #f2e7d8 100%);
  color: var(--ink);
  font: 16px/1.7 var(--sans);
}

a {
  color: var(--accent-strong);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

code,
pre {
  font-family: "SFMono-Regular", "Menlo", "Monaco", "Courier New", monospace;
}

code {
  padding: 0.1rem 0.35rem;
  border-radius: 0.35rem;
  background: var(--accent-soft);
  color: var(--accent);
}

pre {
  margin: 0;
  padding: 1rem 1.1rem;
  overflow: auto;
  border-radius: var(--radius-sm);
  background: #f8f2e9;
  border: 1px solid var(--line);
  color: #283436;
}

.arch-shell {
  width: min(1100px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 24px 0 44px;
}

.hero {
  display: grid;
  gap: 14px;
  margin-bottom: 22px;
}

.hero-card {
  padding: 24px 26px;
  border: 1px solid rgba(204, 184, 156, 0.82);
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(255, 251, 245, 0.98), rgba(252, 246, 237, 0.94));
  box-shadow: var(--shadow);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--warm);
  font-size: 0.82rem;
  font-weight: 700;
}

h1,
h2,
h3,
h4 {
  margin: 0;
  font-family: var(--serif);
  font-weight: 700;
  line-height: 1.15;
}

h1 {
  font-size: clamp(2rem, 3.3vw, 3rem);
}

h2 {
  font-size: clamp(1.6rem, 2vw, 2rem);
}

h3 {
  font-size: 1.15rem;
}

.lede {
  max-width: 760px;
  margin: 0;
  color: var(--muted);
  font-size: 1rem;
}

.version-jump {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.version-jump a {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 0.8rem;
  border-radius: 999px;
  background: rgba(255, 252, 246, 0.86);
  border: 1px solid rgba(204, 184, 156, 0.9);
  color: var(--muted);
  font-weight: 600;
}

.site-grid {
  display: grid;
  gap: 22px;
}

.version-section,
.panel,
.group-block,
.source-block {
  border: 1px solid rgba(204, 184, 156, 0.82);
  border-radius: var(--radius-md);
  background: var(--surface);
  box-shadow: var(--shadow);
}

.version-section {
  padding: 20px;
}

.section-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-note {
  color: var(--muted);
  font-size: 0.95rem;
}

.group-stack {
  display: grid;
  gap: 14px;
}

.group-block {
  padding: 16px;
  background: linear-gradient(180deg, rgba(255, 248, 238, 0.78), rgba(255, 253, 249, 0.98));
}

.group-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--ink);
}

.group-title::before {
  content: "";
  width: 14px;
  height: 14px;
  border-radius: 4px;
  background: var(--accent-soft);
  border: 1px solid rgba(15, 118, 110, 0.18);
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.item-card {
  height: 100%;
  padding: 14px 15px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(221, 205, 184, 0.86);
  background: var(--surface-strong);
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

.item-card:hover {
  transform: translateY(-2px);
  border-color: rgba(15, 118, 110, 0.22);
  box-shadow: 0 16px 28px rgba(42, 55, 58, 0.1);
}

.item-card h3 {
  margin-bottom: 8px;
}

.item-card p {
  margin: 0;
  color: var(--muted);
}

.card-link {
  text-decoration: none;
}

.card-link:hover {
  text-decoration: none;
}

.inline-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel {
  padding: 20px;
}

.item-stack {
  display: grid;
  gap: 22px;
}

.item-stack > * {
  min-width: 0;
}

.item-detail {
  display: grid;
  gap: 22px;
}

.item-detail > * {
  min-width: 0;
}

.prose h1,
.prose h2,
.prose h3,
.prose h4 {
  margin: 1.4em 0 0.55em;
}

.prose h1:first-child,
.prose h2:first-child,
.prose h3:first-child,
.prose h4:first-child {
  margin-top: 0;
}

.prose p,
.prose ul,
.prose ol,
.prose pre {
  margin: 0 0 1rem;
}

.prose ul,
.prose ol {
  padding-left: 1.25rem;
}

.prose li + li {
  margin-top: 0.4rem;
}

.diagram-frame {
  margin: 0;
  padding: 14px;
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, rgba(248, 241, 230, 0.9), rgba(255, 252, 247, 0.98));
  border: 1px solid rgba(221, 205, 184, 0.86);
}

.diagram-scroll {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

.diagram-scroll svg {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  min-width: min(760px, 100%);
}

.diagram-scroll-wide svg {
  width: var(--diagram-wide-width);
  max-width: none;
  min-width: max(100%, var(--diagram-wide-width));
}

.source-grid {
  display: grid;
  gap: 12px;
}

.source-block {
  padding: 16px;
}

.source-block details summary {
  cursor: pointer;
  font-weight: 700;
  color: var(--accent-strong);
}

.source-block details[open] summary {
  margin-bottom: 12px;
}

.breadcrumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 0.92rem;
}

.breadcrumbs span {
  color: var(--line-strong);
}

.empty-state {
  padding: 24px;
  border-radius: var(--radius-md);
  background: rgba(255, 248, 238, 0.96);
  border: 1px dashed rgba(203, 181, 155, 0.9);
  color: var(--muted);
}

.source-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.source-links a {
  display: inline-flex;
  align-items: center;
  padding: 0.42rem 0.75rem;
  border-radius: 999px;
  border: 1px solid rgba(204, 184, 156, 0.85);
  background: rgba(255, 252, 246, 0.88);
  color: var(--muted);
  font-size: 0.9rem;
}

.related-inline {
  margin-top: 14px;
  color: var(--muted);
  font-size: 0.92rem;
}

.related-inline ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

@media (max-width: 920px) {
  .arch-shell {
    width: min(100vw - 20px, 1200px);
    padding-top: 18px;
  }

  .hero-card,
  .panel,
  .version-section,
  .group-block,
  .source-block {
    padding-left: 18px;
    padding-right: 18px;
  }
}
""".strip()

INLINE_PATTERN = re.compile(r"(`[^`]+`|\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*)")


@dataclass(frozen=True)
class VersionRecord:
    id: str
    label: str
    summary: str
    order: int


@dataclass
class ItemRecord:
    root: Path
    version: str
    id: str
    title: str
    summary: str
    group: str
    order: int
    status: str
    tags: list[str]
    links: list[str]
    source_commit: str
    version_label: str
    version_summary: str
    source_path: Path
    svg_path: Path
    doc_path: Path
    page_path: Path

    @property
    def key(self) -> str:
        return f"{self.version}/{self.id}"

    @property
    def page_href(self) -> str:
        return relative_href(self.root, self.page_path)


def load_template() -> Template:
    template_path = Path(__file__).resolve().parent.parent / "templates" / "arch" / "page.html.tmpl"
    return Template(template_path.read_text(encoding="utf-8"))


def ensure_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"invalid catalog: {field} must be a non-empty string")
    return value.strip()


def optional_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise SystemExit("invalid catalog: expected string field")
    return value.strip() or default


def optional_int(value: object, default: int) -> int:
    if value is None:
        return default
    if not isinstance(value, int):
        raise SystemExit("invalid catalog: expected integer field")
    return value


def optional_string_list(value: object, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise SystemExit(f"invalid catalog: {field} must be a list")
    result: list[str] = []
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            raise SystemExit(f"invalid catalog: {field}[{index}] must be a non-empty string")
        result.append(entry.strip())
    return result


def is_item_dir(path: Path) -> bool:
    try:
        content_dir = path.parent.parent
    except IndexError:
        return False
    return path.is_dir() and content_dir.name == "content" and (path / "index.md").exists()


def item_dir_root(path: Path) -> Path:
    if not is_item_dir(path):
        raise SystemExit(f"invalid input: '{path}' is not an item directory")
    return path.parents[2]


def is_item_file(path: Path) -> bool:
    return path.is_file() and path.name in KNOWN_ITEM_FILENAMES and is_item_dir(path.parent)


def resolve_arch_root(raw: str) -> Path:
    path = Path(raw).resolve()
    if path.is_dir():
        if (path / "catalog.json").exists():
            return path
        if is_item_dir(path):
            return item_dir_root(path)
        raise SystemExit(f"invalid input: '{raw}' is neither arch root nor item directory")
    if path.name == "catalog.json" and path.is_file():
        return path.parent
    if is_item_file(path):
        return item_dir_root(path.parent)
    raise SystemExit(f"invalid input: '{raw}' is not supported")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "group"


def relative_href(from_dir: Path, target: Path) -> str:
    return os.path.relpath(target, start=from_dir).replace(os.sep, "/")


def render_inline(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in INLINE_PATTERN.finditer(text):
        parts.append(escape(text[cursor : match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            parts.append(f"<code>{escape(token[1:-1])}</code>")
        elif token.startswith("["):
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", token).groups()  # type: ignore[union-attr]
            parts.append(f'<a href="{escape(url, quote=True)}">{escape(label)}</a>')
        elif token.startswith("**"):
            parts.append(f"<strong>{escape(token[2:-2])}</strong>")
        else:
            parts.append(f"<em>{escape(token[1:-1])}</em>")
        cursor = match.end()
    parts.append(escape(text[cursor:]))
    return "".join(parts)


def markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_type: str | None = None
    in_code = False
    code_lines: list[str] = []
    code_lang = ""

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            blocks.append(f"<p>{render_inline(text)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items, list_type
        if list_items and list_type:
            items_html = "".join(f"<li>{item}</li>" for item in list_items)
            blocks.append(f"<{list_type}>{items_html}</{list_type}>")
            list_items = []
            list_type = None

    def flush_code() -> None:
        nonlocal code_lines, code_lang
        lang_attr = f' class="language-{escape(code_lang, quote=True)}"' if code_lang else ""
        code_html = escape("\n".join(code_lines))
        blocks.append(f"<pre><code{lang_attr}>{code_html}</code></pre>")
        code_lines = []
        code_lang = ""

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                in_code = False
                flush_code()
            else:
                code_lines.append(line)
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            in_code = True
            code_lang = stripped[3:].strip()
            code_lines = []
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            continue

        unordered = re.match(r"^[-*]\s+(.*)$", stripped)
        if unordered:
            flush_paragraph()
            if list_type not in (None, "ul"):
                flush_list()
            list_type = "ul"
            list_items.append(render_inline(unordered.group(1).strip()))
            continue

        ordered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ordered:
            flush_paragraph()
            if list_type not in (None, "ol"):
                flush_list()
            list_type = "ol"
            list_items.append(render_inline(ordered.group(1).strip()))
            continue

        paragraph.append(line)

    flush_paragraph()
    flush_list()
    if in_code:
        raise SystemExit("invalid markdown: unclosed code fence")
    return "\n".join(blocks)


def strip_leading_title(markdown: str, title: str) -> str:
    lines = markdown.splitlines()
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return markdown
    if lines[index].strip() != f"# {title}":
        return markdown
    index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    return "\n".join(lines[index:])


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid json: {path}: {exc}") from exc


def load_site(root: Path) -> tuple[dict, list[VersionRecord], list[ItemRecord]]:
    catalog_path = root / "catalog.json"
    data = read_json(catalog_path)
    if not isinstance(data, dict):
        raise SystemExit(f"invalid catalog: root must be an object in {catalog_path}")
    if data.get("version") != 2:
        raise SystemExit(f"invalid catalog: version must be 2 in {catalog_path}")

    site = data.get("site")
    if not isinstance(site, dict):
        raise SystemExit(f"invalid catalog: site must be an object in {catalog_path}")
    site_id = ensure_text(site.get("id"), "site.id")
    site_title = ensure_text(site.get("title"), "site.title")
    site_summary = optional_text(site.get("summary"))
    default_version = optional_text(site.get("default_version"))

    versions_raw = data.get("versions")
    if not isinstance(versions_raw, list):
        raise SystemExit(f"invalid catalog: versions must be a list in {catalog_path}")
    version_map: dict[str, VersionRecord] = {}
    for index, entry in enumerate(versions_raw):
        if not isinstance(entry, dict):
            raise SystemExit(f"invalid catalog: versions[{index}] must be an object")
        version_id = ensure_text(entry.get("id"), f"versions[{index}].id")
        if version_id in version_map:
            raise SystemExit(f"invalid catalog: duplicate version id '{version_id}'")
        version_map[version_id] = VersionRecord(
            id=version_id,
            label=ensure_text(entry.get("label"), f"versions[{index}].label"),
            summary=optional_text(entry.get("summary")),
            order=optional_int(entry.get("order"), (index + 1) * 10),
        )

    if default_version and default_version not in version_map:
        raise SystemExit(f"invalid catalog: site.default_version '{default_version}' is unknown")

    items_raw = data.get("items")
    if not isinstance(items_raw, list):
        raise SystemExit(f"invalid catalog: items must be a list in {catalog_path}")

    items: list[ItemRecord] = []
    seen_keys: set[str] = set()
    for index, entry in enumerate(items_raw):
        if not isinstance(entry, dict):
            raise SystemExit(f"invalid catalog: items[{index}] must be an object")
        version_id = ensure_text(entry.get("version"), f"items[{index}].version")
        if version_id not in version_map:
            raise SystemExit(f"invalid catalog: items[{index}].version '{version_id}' is unknown")
        item_id = ensure_text(entry.get("id"), f"items[{index}].id")
        key = f"{version_id}/{item_id}"
        if key in seen_keys:
            raise SystemExit(f"invalid catalog: duplicate item key '{key}'")
        seen_keys.add(key)

        item_dir = root / "content" / version_id / item_id
        doc_path = item_dir / "index.md"
        if not doc_path.exists():
            raise SystemExit(f"missing source: {doc_path}")
        svg_path = item_dir / "diagram.svg"
        if not svg_path.exists():
            raise SystemExit(f"missing source: {svg_path}")

        source_paths = [item_dir / f"diagram.{ext}" for ext in SOURCE_LABELS if (item_dir / f"diagram.{ext}").exists()]
        if len(source_paths) != 1:
            raise SystemExit(f"invalid source set: {item_dir} must contain exactly one diagram.<source> file")
        source_path = source_paths[0]

        version_info = version_map[version_id]
        items.append(
            ItemRecord(
                root=root,
                version=version_id,
                id=item_id,
                title=ensure_text(entry.get("title"), f"items[{index}].title"),
                summary=optional_text(entry.get("summary")),
                group=optional_text(entry.get("group"), "Ungrouped"),
                order=optional_int(entry.get("order"), (index + 1) * 10),
                status=optional_text(entry.get("status"), "draft"),
                tags=optional_string_list(entry.get("tags"), f"items[{index}].tags"),
                links=optional_string_list(entry.get("links"), f"items[{index}].links"),
                source_commit=optional_text(entry.get("source_commit"), "-"),
                version_label=version_info.label,
                version_summary=version_info.summary,
                source_path=source_path,
                svg_path=svg_path,
                doc_path=doc_path,
                page_path=item_dir / "index.html",
            )
        )

    item_map = {item.key: item for item in items}
    for item in items:
        for link in item.links:
            if "/" not in link:
                raise SystemExit(f"invalid catalog: item '{item.key}' link '{link}' must use version/id form")
            if link not in item_map:
                raise SystemExit(f"invalid catalog: item '{item.key}' links unknown item '{link}'")

    site_info = {
        "id": site_id,
        "title": site_title,
        "summary": site_summary,
        "default_version": default_version or (sorted(version_map.values(), key=lambda entry: (entry.order, entry.label, entry.id))[0].id if version_map else ""),
    }
    versions = sorted(version_map.values(), key=lambda entry: (entry.order, entry.label, entry.id))
    items.sort(key=lambda entry: (version_map[entry.version].order, entry.group.lower(), entry.order, entry.title.lower(), entry.id))
    return site_info, versions, items


def validate_svg(path: Path) -> str:
    svg = path.read_text(encoding="utf-8")
    if "<svg" not in svg:
        raise SystemExit(f"invalid svg: {path} does not contain <svg")
    return svg


def svg_intrinsic_width(svg: str) -> float | None:
    match = SVG_OPEN_TAG_PATTERN.search(svg)
    if not match:
        return None
    attrs = match.group(1)

    viewbox_match = SVG_VIEWBOX_PATTERN.search(attrs)
    if viewbox_match:
        parts = [part for part in re.split(r"[\s,]+", viewbox_match.group(1).strip()) if part]
        if len(parts) == 4:
            try:
                return float(parts[2])
            except ValueError:
                return None

    width_match = SVG_WIDTH_PATTERN.search(attrs)
    if width_match:
        try:
            return float(width_match.group(1))
        except ValueError:
            return None

    style_match = SVG_STYLE_MAX_WIDTH_PATTERN.search(attrs)
    if style_match:
        try:
            return float(style_match.group(1))
        except ValueError:
            return None

    return None


def diagram_scroll_attrs(svg: str) -> str:
    width = svg_intrinsic_width(svg)
    if width is None or width <= WIDE_DIAGRAM_THRESHOLD:
        return 'class="diagram-scroll"'
    width_px = max(int(round(width)), int(WIDE_DIAGRAM_THRESHOLD))
    return f'class="diagram-scroll diagram-scroll-wide" style="--diagram-wide-width: {width_px}px;"'


def render_page(template: Template, page_title: str, stylesheet_href: str, page_class: str, body_html: str) -> str:
    return template.substitute(
        page_title=page_title,
        stylesheet_href=stylesheet_href,
        page_class=page_class,
        body_html=body_html,
    )


def render_root_body(site: dict, versions: list[VersionRecord], items: list[ItemRecord]) -> str:
    by_version: dict[str, list[ItemRecord]] = {}
    for version in versions:
        by_version[version.id] = [item for item in items if item.version == version.id]

    jump_links = "".join(
        f'<a href="#version-{escape(version.id)}">{escape(version.label)} · {len(by_version[version.id])}</a>' for version in versions
    )
    site_lede = f'<p class="lede">{escape(site["summary"])}</p>' if site.get("summary") else ""

    sections: list[str] = []
    for version in versions:
        version_items = by_version[version.id]
        grouped: dict[str, list[ItemRecord]] = {}
        for item in version_items:
            grouped.setdefault(item.group, []).append(item)

        group_blocks: list[str] = []
        for group_name in sorted(grouped, key=lambda value: (value.lower(), value)):
            cards = []
            for item in sorted(grouped[group_name], key=lambda entry: (entry.order, entry.title.lower(), entry.id)):
                card_note = f'<p class="section-note">{escape(", ".join(item.tags))}</p>' if item.tags else ""
                cards.append(
                    f"""
<article class="item-card">
  <h3><a class="card-link" href="{escape(item.page_href, quote=True)}">{escape(item.title)}</a></h3>
  <p>{escape(item.summary or '暂无摘要。')}</p>
  {card_note}
</article>
""".strip()
                )
            group_blocks.append(
                f"""
<section class="group-block">
  <div class="group-title"><h3>{escape(group_name)}</h3></div>
  <div class="cards">
    {''.join(cards)}
  </div>
</section>
""".strip()
            )

        if not group_blocks:
            group_blocks.append('<div class="empty-state">当前版本还没有 item，先创建 `content/&lt;version&gt;/&lt;item&gt;/` 与 `catalog.json` 条目。</div>')

        summary_html = f'<p class="section-note">{escape(version.summary)}</p>' if version.summary else ""
        sections.append(
            f"""
<section class="version-section" id="version-{escape(version.id, quote=True)}">
  <div class="section-head">
    <div>
      <h2>{escape(version.label)}</h2>
      {summary_html}
    </div>
    <p class="section-note">{len(version_items)} 个条目</p>
  </div>
  <div class="group-stack">
    {''.join(group_blocks)}
  </div>
</section>
""".strip()
        )

    if not sections:
        sections.append('<div class="empty-state">站点还没有 version 和 item。先补 `catalog.json` 与 `content/` 再执行 renderer。</div>')

    return f"""
<main class="arch-shell">
  <header class="hero">
    <div class="hero-card">
      <h1>{escape(site['title'])}</h1>
      {site_lede}
    </div>
    <div class="version-jump">{jump_links}</div>
  </header>
  <section class="site-grid">
    {''.join(sections)}
  </section>
</main>
""".strip()


def render_related_items(item: ItemRecord, item_map: dict[str, ItemRecord]) -> str:
    if not item.links:
        return ""
    entries: list[str] = []
    for ref in item.links:
        linked = item_map[ref]
        href = relative_href(item.page_path.parent, linked.page_path)
        entries.append(f'<li><a href="{escape(href, quote=True)}">{escape(linked.title)}</a></li>')
    return f"<ul>{''.join(entries)}</ul>"


def render_item_body(item: ItemRecord, item_map: dict[str, ItemRecord]) -> str:
    root_index = item.root / "index.html"
    stylesheet_href = relative_href(item.page_path.parent, item.root / "assets" / "arch.css")
    markdown_source = item.doc_path.read_text(encoding="utf-8")
    markdown_html = markdown_to_html(strip_leading_title(markdown_source, item.title))
    svg_html = validate_svg(item.svg_path)
    scroll_attrs = diagram_scroll_attrs(svg_html)
    source_code = escape(item.source_path.read_text(encoding="utf-8"))
    back_href = relative_href(item.page_path.parent, root_index)
    item_lede_text = item.summary or item.version_summary or ""
    item_lede = f'<p class="lede">{escape(item_lede_text)}</p>' if item_lede_text else ""
    related_html = render_related_items(item, item_map)
    related_block = (
        f"""
<div class="related-inline">
        <strong>关联条目</strong>
        {related_html}
      </div>"""
        if related_html
        else ""
    )

    raw_doc_href = relative_href(item.page_path.parent, item.doc_path)
    raw_svg_href = relative_href(item.page_path.parent, item.svg_path)
    raw_source_href = relative_href(item.page_path.parent, item.source_path)

    body_html = f"""
<main class="arch-shell">
  <header class="hero">
    <div class="hero-card">
      <nav class="breadcrumbs">
        <a href="{escape(back_href, quote=True)}">架构</a>
        <span>/</span>
        <a href="{escape(back_href, quote=True)}#version-{escape(item.version, quote=True)}">{escape(item.version_label)}</a>
        <span>/</span>
        <strong>{escape(item.title)}</strong>
      </nav>
      <div class="eyebrow">{escape(item.group)}</div>
      <h1>{escape(item.title)}</h1>
      {item_lede}
      <div class="source-links">
        <a href="{escape(raw_doc_href, quote=True)}">index.md</a>
        <a href="{escape(raw_source_href, quote=True)}">{escape(item.source_path.name)}</a>
        <a href="{escape(raw_svg_href, quote=True)}">diagram.svg</a>
      </div>
    </div>
  </header>

  <div class="item-stack">
    <section class="panel item-detail">
      <article class="prose">
        {markdown_html}
      </article>
      <section>
        <div class="section-head">
          <div>
            <h2>图示</h2>
          </div>
        </div>
        <figure class="diagram-frame">
          <div {scroll_attrs}>
            {svg_html}
          </div>
        </figure>
      </section>
{related_block}
    </section>

    <section class="source-grid">
      <section class="source-block">
        <details open>
          <summary>{escape(item.source_path.name)} 图源</summary>
          <pre><code>{source_code}</code></pre>
        </details>
      </section>
    </section>
  </div>
</main>
""".strip()

    return render_page(
        load_template(),
        page_title=item.title,
        stylesheet_href=stylesheet_href,
        page_class="item-page",
        body_html=body_html,
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_if_needed(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")


def render_site(root: Path, check_only: bool) -> None:
    site, versions, items = load_site(root)
    item_map = {item.key: item for item in items}
    template = load_template()

    root_body = render_root_body(site, versions, items)
    root_html = render_page(
        template,
        page_title=site["title"],
        stylesheet_href="assets/arch.css",
        page_class="root-page",
        body_html=root_body,
    )

    item_pages = {item.page_path: render_item_body(item, item_map) for item in items}

    if check_only:
        print(f"arch_render:PASS:{root}")
        return

    write_if_needed(root / "assets" / "arch.css", CSS_CONTENT)
    write_if_needed(root / "index.html", root_html)
    for page_path, html in item_pages.items():
        write_if_needed(page_path, html)
    print(f"arch_render:WROTE:{root}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render source-first static architecture sites")
    parser.add_argument("target", help="arch root, catalog.json, item directory, or item source file")
    parser.add_argument("--check", action="store_true", help="validate source layout without writing files")
    args = parser.parse_args()

    root = resolve_arch_root(args.target)
    render_site(root, check_only=args.check)


if __name__ == "__main__":
    main()
