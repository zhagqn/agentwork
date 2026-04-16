#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from html import escape
import math
from pathlib import Path
from string import Template
import sys
import unicodedata


PALETTE = {
    "frontend": ("rgba(8, 51, 68, 0.40)", "#22d3ee"),
    "backend": ("rgba(6, 78, 59, 0.40)", "#34d399"),
    "database": ("rgba(76, 29, 149, 0.40)", "#a78bfa"),
    "cloud": ("rgba(120, 53, 15, 0.30)", "#fbbf24"),
    "security": ("rgba(136, 19, 55, 0.40)", "#fb7185"),
    "message": ("rgba(251, 146, 60, 0.30)", "#fb923c"),
    "actor": ("rgba(30, 41, 59, 0.55)", "#cbd5e1"),
    "external": ("rgba(30, 41, 59, 0.55)", "#94a3b8"),
    "generic": ("rgba(30, 41, 59, 0.55)", "#94a3b8"),
}

FONT_STACK = (
    '"SF Pro Text", "SF Pro Display", "PingFang SC", "Hiragino Sans GB", '
    '"Microsoft YaHei", "Noto Sans CJK SC", "Segoe UI", sans-serif'
)
DEFAULT_VIEWPORT_WIDTH = 1120
DEFAULT_VIEWPORT_HEIGHT = 700
DEFAULT_CANVAS_PADDING = 30.0


def load_template(template_path: Path) -> Template:
    return Template(template_path.read_text(encoding="utf-8"))


def resolve_diagram_path(raw: str) -> Path:
    path = Path(raw).resolve()
    if path.is_dir():
        path = path / "diagram.arch.json"
    return path


def load_diagram(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("nodes"), list) or not data["nodes"]:
        raise SystemExit(f"invalid diagram: missing nodes in {path}")
    if not isinstance(data.get("edges", []), list):
        raise SystemExit(f"invalid diagram: edges must be a list in {path}")
    return data


def palette_for(kind: str | None) -> tuple[str, str]:
    return PALETTE.get((kind or "generic").lower(), PALETTE["generic"])


def child_href_map(children: list[dict]) -> dict[str, str]:
    hrefs: dict[str, str] = {}
    for child in children:
        node_id = child.get("node_id")
        child_path = child.get("path")
        if not node_id or not child_path:
            continue
        hrefs[str(node_id)] = f"{child_path.rstrip('/')}/index.html"
    return hrefs


def parent_href(diagram_path: Path) -> str | None:
    current_dir = diagram_path.parent
    if len(current_dir.parts) >= 2 and current_dir.parent.name == "nodes":
        return "../../index.html"
    return None


def node_centers(nodes: list[dict]) -> dict[str, tuple[float, float]]:
    centers: dict[str, tuple[float, float]] = {}
    for node in nodes:
        centers[str(node["id"])] = (
            float(node["x"]) + float(node.get("w", 180)) / 2.0,
            float(node["y"]) + float(node.get("h", 88)) / 2.0,
        )
    return centers


def node_boxes(nodes: list[dict]) -> dict[str, dict[str, float]]:
    boxes: dict[str, dict[str, float]] = {}
    for node in nodes:
        boxes[str(node["id"])] = {
            "x": float(node["x"]),
            "y": float(node["y"]),
            "w": float(node.get("w", 180)),
            "h": float(node.get("h", 88)),
        }
    return boxes


def canvas_size(diagram: dict, nodes: list[dict]) -> tuple[int, int]:
    viewport = diagram.get("viewport", {})
    min_width = int(viewport.get("min_width", viewport.get("width", DEFAULT_VIEWPORT_WIDTH)))
    min_height = int(viewport.get("min_height", viewport.get("height", DEFAULT_VIEWPORT_HEIGHT)))
    padding = float(viewport.get("content_padding", viewport.get("padding", DEFAULT_CANVAS_PADDING)))
    max_right = max(float(node["x"]) + float(node.get("w", 180)) for node in nodes)
    max_bottom = max(float(node["y"]) + float(node.get("h", 88)) for node in nodes)
    width = max(min_width, math.ceil(max_right + padding))
    height = max(min_height, math.ceil(max_bottom + padding))
    return width, height


def display_units(text: str) -> int:
    units = 0
    for char in text:
        units += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return max(units, 1)


def rects_overlap(a: dict[str, float], b: dict[str, float], gap: float = 0.0) -> bool:
    return not (
        a["x"] + a["w"] <= b["x"] - gap
        or b["x"] + b["w"] <= a["x"] - gap
        or a["y"] + a["h"] <= b["y"] - gap
        or b["y"] + b["h"] <= a["y"] - gap
    )


def clamp_label_rect(
    raw_cx: float,
    raw_cy: float,
    label_width: float,
    label_height: float,
    width: float,
    height: float,
    margin: float,
) -> tuple[float, float, dict[str, float], bool]:
    label_cx = min(max(raw_cx, margin + label_width / 2), width - margin - label_width / 2)
    label_cy = min(max(raw_cy, margin + label_height / 2), height - margin - label_height / 2)
    return (
        label_cx,
        label_cy,
        {
            "x": label_cx - label_width / 2,
            "y": label_cy - label_height / 2,
            "w": label_width,
            "h": label_height,
        },
        abs(label_cx - raw_cx) > 0.1 or abs(label_cy - raw_cy) > 0.1,
    )


def place_edge_label(
    mid_x: float,
    mid_y: float,
    normal_x: float,
    normal_y: float,
    base_offset: float,
    label_width: float,
    label_height: float,
    width: float,
    height: float,
    boxes: dict[str, dict[str, float]],
) -> tuple[float, float, float, float]:
    margin = 10.0
    candidates: list[tuple[int, int, int, float, float, dict[str, float]]] = []
    for direction in (-1.0, 1.0):
        for step in range(7):
            offset = base_offset + step * 14.0
            raw_cx = mid_x + normal_x * offset * direction
            raw_cy = mid_y + normal_y * offset * direction
            label_cx, label_cy, rect, was_clamped = clamp_label_rect(
                raw_cx,
                raw_cy,
                label_width,
                label_height,
                width,
                height,
                margin,
            )
            overlap_count = sum(1 for box in boxes.values() if rects_overlap(rect, box, gap=6.0))
            candidates.append((overlap_count, 1 if was_clamped else 0, step, label_cx, label_cy, rect))
            if overlap_count == 0 and not was_clamped:
                return rect["x"], rect["y"], label_cx, label_cy
    best = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    rect = best[5]
    return rect["x"], rect["y"], best[3], best[4]


def anchor_point(
    box: dict[str, float],
    center: tuple[float, float],
    other_center: tuple[float, float],
) -> tuple[float, float]:
    dx = other_center[0] - center[0]
    dy = other_center[1] - center[1]
    if dx == 0 and dy == 0:
        return center
    half_w = box["w"] / 2.0
    half_h = box["h"] / 2.0
    scale = max(abs(dx) / half_w if half_w else 0.0, abs(dy) / half_h if half_h else 0.0, 1.0)
    return center[0] + dx / scale, center[1] + dy / scale


def render_edge_layers(
    edges: list[dict],
    centers: dict[str, tuple[float, float]],
    boxes: dict[str, dict[str, float]],
    width: float,
    height: float,
) -> tuple[str, str]:
    line_parts: list[str] = []
    label_parts: list[str] = []
    for index, edge in enumerate(edges):
        source_id = str(edge.get("from"))
        target_id = str(edge.get("to"))
        source_center = centers.get(source_id)
        target_center = centers.get(target_id)
        source_box = boxes.get(source_id)
        target_box = boxes.get(target_id)
        if not source_center or not target_center or not source_box or not target_box:
            continue
        source = anchor_point(source_box, source_center, target_center)
        target = anchor_point(target_box, target_center, source_center)
        dash = ' stroke-dasharray="6,4"' if edge.get("style") == "dashed" else ""
        color = escape(edge.get("color", "#7dd3fc"))
        label = edge.get("label")
        dx = target[0] - source[0]
        dy = target[1] - source[1]
        edge_len = max((dx * dx + dy * dy) ** 0.5, 1.0)
        mid_x = (source[0] + target[0]) / 2
        mid_y = (source[1] + target[1]) / 2
        line_parts.append(
            f'<line class="edge edge-{index}" x1="{source[0]:.1f}" y1="{source[1]:.1f}" '
            f'x2="{target[0]:.1f}" y2="{target[1]:.1f}" stroke="{color}" stroke-width="1.6"'
            f'{dash} marker-end="url(#arrowhead)" />'
        )
        if label:
            label_text = str(label)
            label_width = max(46.0, display_units(label_text) * 6.8 + 18.0)
            label_height = 24.0
            offset = 18.0 if edge_len >= label_width + 32.0 else 28.0
            normal_x = -dy / edge_len
            normal_y = dx / edge_len
            label_x, label_y, label_cx, label_cy = place_edge_label(
                mid_x,
                mid_y,
                normal_x,
                normal_y,
                offset,
                label_width,
                label_height,
                width,
                height,
                boxes,
            )
            label_parts.append(
                '<g class="edge-label-group">'
                f'<rect class="edge-label-bg" x="{label_x:.1f}" y="{label_y:.1f}" '
                f'width="{label_width:.1f}" height="{label_height:.1f}" rx="9" />'
                f'<text class="edge-label" x="{label_cx:.1f}" y="{label_cy + 4.0:.1f}" '
                f'text-anchor="middle">{escape(label_text)}</text>'
                '</g>'
            )
    return "\n".join(line_parts), "\n".join(label_parts)


def render_node(node: dict, href: str | None) -> str:
    x = float(node["x"])
    y = float(node["y"])
    w = float(node.get("w", 180))
    h = float(node.get("h", 88))
    fill, stroke = palette_for(node.get("kind"))
    label = escape(str(node.get("label", node["id"])))
    lines = [escape(str(item)) for item in node.get("lines", [])][:4]
    badge = "Open child" if href else node.get("badge", "")
    inner: list[str] = [
        f'<g class="node-body {"is-linked" if href else ""}" data-node-id="{escape(str(node["id"]))}">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="#09111f" />',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="1.6" />',
        f'<text class="node-title" x="{x + w / 2:.1f}" y="{y + 26:.1f}" text-anchor="middle">{label}</text>',
    ]
    for index, line in enumerate(lines):
        inner.append(
            f'<text class="node-line" x="{x + w / 2:.1f}" y="{y + 49 + index * 17:.1f}" '
            f'text-anchor="middle">{line}</text>'
        )
    if badge:
        inner.append(
            f'<text class="node-badge" x="{x + w / 2:.1f}" y="{y + h - 12:.1f}" text-anchor="middle">{escape(str(badge))}</text>'
        )
    inner.append("</g>")
    body = "\n".join(inner)
    if not href:
        return body
    return f'<a href="{escape(href)}" class="node-link">{body}</a>'


def render_nodes(nodes: list[dict], hrefs: dict[str, str]) -> str:
    return "\n".join(render_node(node, hrefs.get(str(node["id"]))) for node in nodes)


def render_cards(cards: list[dict]) -> str:
    if not cards:
        cards = [
            {
                "title": "Summary",
                "items": ["No cards provided", "Add cards[] in diagram.arch.json"],
            }
        ]
    parts: list[str] = []
    for card in cards:
        title = escape(str(card.get("title", "Card")))
        items = card.get("items", [])
        list_items = "\n".join(
            f"<li>{escape(str(item))}</li>" for item in items[:5]
        )
        parts.append(
            "<section class=\"card\">"
            f"<h3>{title}</h3>"
            f"<ul>{list_items}</ul>"
            "</section>"
        )
    return "\n".join(parts)


def render_breadcrumb(title: str, parent_link: str | None) -> str:
    crumb = '<span>Overview</span>' if not parent_link else f'<a href="{escape(parent_link)}">Back</a>'
    return f'<nav class="breadcrumb">{crumb}<span>/</span><span>{escape(title)}</span></nav>'


def build_svg(diagram: dict, diagram_path: Path) -> str:
    children = diagram.get("children", [])
    hrefs = child_href_map(children)
    nodes = diagram["nodes"]
    width, height = canvas_size(diagram, nodes)
    centers = node_centers(nodes)
    boxes = node_boxes(nodes)
    edge_lines_html, edge_labels_html = render_edge_layers(diagram.get("edges", []), centers, boxes, width, height)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(str(diagram.get("title", "Architecture")))}">'
        "<defs>"
        '<marker id="arrowhead" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">'
        '<polygon points="0 0, 12 4, 0 8" fill="#7dd3fc" />'
        "</marker>"
        '<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        '<path d="M 40 0 L 0 0 0 40" fill="none" stroke="#15304b" stroke-width="0.8" opacity="0.55" />'
        "</pattern>"
        "</defs>"
        '<rect width="100%" height="100%" fill="url(#grid)" />'
        f"{edge_lines_html}"
        f"{render_nodes(nodes, hrefs)}"
        f"{edge_labels_html}"
        "</svg>"
    )


def render_diagram(diagram_path: Path, template_path: Path) -> Path:
    diagram = load_diagram(diagram_path)
    svg_html = build_svg(diagram, diagram_path)
    cards_html = render_cards(diagram.get("cards", []))
    title = str(diagram.get("title", "Architecture"))
    summary = str(diagram.get("summary", ""))
    updated_at = str(diagram.get("meta", {}).get("updated_at", ""))
    footer = escape(updated_at) if updated_at else escape(str(diagram_path.relative_to(Path.cwd()))) if diagram_path.is_relative_to(Path.cwd()) else escape(str(diagram_path))
    breadcrumb_html = render_breadcrumb(title, parent_href(diagram_path))
    html = load_template(template_path).safe_substitute(
        page_title=escape(title),
        title=escape(title),
        subtitle=escape(summary),
        breadcrumb_html=breadcrumb_html,
        svg_html=svg_html,
        cards_html=cards_html,
        footer=footer,
        font_stack=FONT_STACK,
    )
    output_path = diagram_path.with_name("index.html")
    output_path.write_text(html, encoding="utf-8")
    return output_path


def render_recursive(diagram_path: Path, template_path: Path, seen: set[Path]) -> list[Path]:
    diagram_path = diagram_path.resolve()
    if diagram_path in seen:
        return []
    seen.add(diagram_path)
    outputs = [render_diagram(diagram_path, template_path)]
    diagram = load_diagram(diagram_path)
    for child in diagram.get("children", []):
        child_path = child.get("path")
        if not child_path:
            continue
        child_diagram = (diagram_path.parent / child_path / "diagram.arch.json").resolve()
        if not child_diagram.exists():
            raise SystemExit(f"missing child diagram for {diagram_path}: {child_diagram}")
        outputs.extend(render_recursive(child_diagram, template_path, seen))
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render diagram.arch.json into static index.html files.")
    parser.add_argument("diagram", help="diagram.arch.json path or a directory that contains it")
    parser.add_argument("--recursive", action="store_true", help="render child diagrams recursively")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    diagram_path = resolve_diagram_path(args.diagram)
    if not diagram_path.exists():
        print(f"missing diagram: {diagram_path}", file=sys.stderr)
        return 2
    template_path = Path(__file__).resolve().parent.parent / "templates" / "architecture" / "page.html.tmpl"
    outputs = (
        render_recursive(diagram_path, template_path, set())
        if args.recursive
        else [render_diagram(diagram_path, template_path)]
    )
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
