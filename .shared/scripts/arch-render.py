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

EDGE_PALETTE = {
    "sync": "#7dd3fc",
    "data": "#38bdf8",
    "read": "#a78bfa",
    "write": "#34d399",
    "control": "#fb7185",
    "async": "#fb923c",
    "event": "#fb923c",
    "dependency": "#94a3b8",
}

FONT_STACK = (
    '"SF Pro Text", "SF Pro Display", "PingFang SC", "Hiragino Sans GB", '
    '"Microsoft YaHei", "Noto Sans CJK SC", "Segoe UI", sans-serif'
)
DEFAULT_VIEWPORT_WIDTH = 1120
DEFAULT_VIEWPORT_HEIGHT = 700
DEFAULT_CANVAS_PADDING = 30.0
DEFAULT_NODE_WIDTH = 180.0
DEFAULT_NODE_HEIGHT = 96.0

DEFAULT_LAYOUT = {
    "direction": "lr",
    "margin_x": 64.0,
    "margin_y": 72.0,
    "rank_gap": 96.0,
    "node_gap": 44.0,
    "group_padding_x": 28.0,
    "group_padding_y": 56.0,
    "min_group_width": 210.0,
}


def load_template(template_path: Path) -> Template:
    return Template(template_path.read_text(encoding="utf-8"))


def resolve_input_path(raw: str) -> Path:
    path = Path(raw).resolve()
    if path.is_dir():
        catalog_path = path / "catalog.json"
        if catalog_path.exists():
            return catalog_path
        diagram_path = path / "diagram.arch.json"
        if diagram_path.exists():
            return diagram_path
        path = path / "diagram.mmd"
    return path


def is_catalog_path(path: Path) -> bool:
    return path.name == "catalog.json"


def group_node_ids(group: dict) -> list[str]:
    raw = group.get("node_ids", group.get("nodes", []))
    if not raw:
        return []
    if not isinstance(raw, list):
        raise SystemExit("invalid diagram: group node_ids must be a list")
    return [str(item) for item in raw]


def validate_diagram(data: dict, path: Path) -> None:
    if not isinstance(data, dict):
        raise SystemExit(f"invalid diagram: root must be an object in {path}")

    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise SystemExit(f"invalid diagram: missing nodes in {path}")

    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise SystemExit(f"invalid diagram: node #{index + 1} must be an object in {path}")
        node_id = node.get("id")
        if not node_id:
            raise SystemExit(f"invalid diagram: node #{index + 1} is missing id in {path}")
        node_id = str(node_id)
        if node_id in node_ids:
            raise SystemExit(f"invalid diagram: duplicate node id '{node_id}' in {path}")
        node_ids.add(node_id)
        if ("x" in node) != ("y" in node):
            raise SystemExit(f"invalid diagram: node '{node_id}' must define both x and y or neither in {path}")

    edges = data.get("edges", [])
    if not isinstance(edges, list):
        raise SystemExit(f"invalid diagram: edges must be a list in {path}")
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise SystemExit(f"invalid diagram: edge #{index + 1} must be an object in {path}")
        source_id = edge.get("from")
        target_id = edge.get("to")
        if not source_id or not target_id:
            raise SystemExit(f"invalid diagram: edge #{index + 1} must define from and to in {path}")
        if str(source_id) not in node_ids or str(target_id) not in node_ids:
            raise SystemExit(f"invalid diagram: edge #{index + 1} references an unknown node in {path}")

    groups = data.get("groups", [])
    if groups and not isinstance(groups, list):
        raise SystemExit(f"invalid diagram: groups must be a list in {path}")
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise SystemExit(f"invalid diagram: group #{index + 1} must be an object in {path}")
        for node_id in group_node_ids(group):
            if node_id not in node_ids:
                raise SystemExit(f"invalid diagram: group #{index + 1} references unknown node '{node_id}' in {path}")

    children = data.get("children", [])
    if children and not isinstance(children, list):
        raise SystemExit(f"invalid diagram: children must be a list in {path}")
    for index, child in enumerate(children):
        if not isinstance(child, dict):
            raise SystemExit(f"invalid diagram: child #{index + 1} must be an object in {path}")
        node_id = child.get("node_id")
        child_path = child.get("path")
        if not node_id or not child_path:
            raise SystemExit(f"invalid diagram: child #{index + 1} must define node_id and path in {path}")
        if str(node_id) not in node_ids:
            raise SystemExit(f"invalid diagram: child #{index + 1} references unknown node '{node_id}' in {path}")


def load_diagram(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_diagram(data, path)
    return data


def load_catalog(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_catalog(data, path)
    return data


def catalog_diagrams(catalog: dict, catalog_path: Path) -> list[dict]:
    diagrams = catalog.get("diagrams")
    if not isinstance(diagrams, list):
        raise SystemExit(f"invalid catalog: diagrams must be a list in {catalog_path}")
    for index, item in enumerate(diagrams):
        if not isinstance(item, dict):
            raise SystemExit(f"invalid catalog: diagram #{index + 1} must be an object in {catalog_path}")
    return diagrams


def catalog_id(item: dict) -> str:
    return str(item.get("id", "")).strip()


def catalog_href_target(root: Path, item: dict) -> Path:
    diagram_id = catalog_id(item) or "<unknown>"
    raw_href = str(item.get("href", "")).strip()
    if not raw_href:
        raise SystemExit(f"invalid catalog: diagram '{diagram_id}' is missing href")
    if raw_href.startswith("/") or "://" in raw_href:
        raise SystemExit(f"invalid catalog: diagram '{diagram_id}' href must be relative")
    href_path = raw_href.split("#", 1)[0].split("?", 1)[0]
    target = (root / href_path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise SystemExit(f"invalid catalog: diagram '{diagram_id}' href escapes arch root")
    if target == (root / "index.html").resolve():
        raise SystemExit("invalid catalog: root index.html is reserved for navigation")
    return target


def source_for_catalog_item(root: Path, item: dict) -> tuple[str, Path] | None:
    target = catalog_href_target(root, item)
    diagram_dir = target.parent
    arch_source = diagram_dir / "diagram.arch.json"
    if arch_source.exists():
        if target != arch_source.with_name("index.html").resolve():
            diagram_id = catalog_id(item) or "<unknown>"
            raise SystemExit(f"invalid catalog: diagram '{diagram_id}' href must point to its source directory index.html")
        return "arch", arch_source
    mermaid_source = diagram_dir / "diagram.mmd"
    if mermaid_source.exists():
        if target != mermaid_source.with_name("index.html").resolve():
            diagram_id = catalog_id(item) or "<unknown>"
            raise SystemExit(f"invalid catalog: diagram '{diagram_id}' href must point to its source directory index.html")
        return "mermaid", mermaid_source
    if target.exists():
        return None
    diagram_id = catalog_id(item) or "<unknown>"
    raise SystemExit(f"invalid catalog: diagram '{diagram_id}' href has no index.html or source file")


def validate_catalog(catalog: dict, catalog_path: Path) -> None:
    if not isinstance(catalog, dict):
        raise SystemExit(f"invalid catalog: root must be an object in {catalog_path}")

    root = catalog_path.parent.resolve()
    diagrams = catalog_diagrams(catalog, catalog_path)
    seen_ids: set[str] = set()
    parent_by_id: dict[str, str] = {}

    for index, item in enumerate(diagrams):
        diagram_id = catalog_id(item)
        if not diagram_id:
            raise SystemExit(f"invalid catalog: diagram #{index + 1} is missing id in {catalog_path}")
        if diagram_id in seen_ids:
            raise SystemExit(f"invalid catalog: duplicate diagram id '{diagram_id}' in {catalog_path}")
        seen_ids.add(diagram_id)
        if not str(item.get("title", "")).strip():
            raise SystemExit(f"invalid catalog: diagram '{diagram_id}' is missing title")
        catalog_href_target(root, item)
        parent_id = str(item.get("parent_id", "")).strip()
        if parent_id:
            parent_by_id[diagram_id] = parent_id
        links = item.get("links", [])
        if links and not isinstance(links, list):
            raise SystemExit(f"invalid catalog: diagram '{diagram_id}' links must be a list")

    for diagram_id, parent_id in parent_by_id.items():
        if parent_id not in seen_ids:
            raise SystemExit(f"invalid catalog: diagram '{diagram_id}' references unknown parent '{parent_id}'")
        if parent_id == diagram_id:
            raise SystemExit(f"invalid catalog: diagram '{diagram_id}' cannot be its own parent")

    for item in diagrams:
        diagram_id = catalog_id(item)
        for link_id in item.get("links", []):
            link_id = str(link_id)
            if link_id not in seen_ids:
                raise SystemExit(f"invalid catalog: diagram '{diagram_id}' links unknown diagram '{link_id}'")

    for diagram_id in seen_ids:
        chain: set[str] = set()
        current = diagram_id
        while current in parent_by_id:
            if current in chain:
                raise SystemExit(f"invalid catalog: parent cycle detected at '{diagram_id}'")
            chain.add(current)
            current = parent_by_id[current]


def palette_for(kind: str | None) -> tuple[str, str]:
    return PALETTE.get((kind or "generic").lower(), PALETTE["generic"])


def edge_kind(edge: dict) -> str:
    raw = edge.get("flow", edge.get("kind", edge.get("type", "")))
    return str(raw).lower()


def edge_color(edge: dict) -> str:
    return str(edge.get("color") or EDGE_PALETTE.get(edge_kind(edge), EDGE_PALETTE["sync"]))


def edge_dash(edge: dict) -> str:
    style = str(edge.get("style", "")).lower()
    kind = edge_kind(edge)
    if style == "dashed" or kind in {"async", "event", "dependency"}:
        return ' stroke-dasharray="6,4"'
    return ""


def marker_id_for_color(color: str) -> str:
    safe = "".join(char if char.isalnum() else "-" for char in color.lower()).strip("-")
    return f"arrow-{safe or 'default'}"


def render_edge_markers(edges: list[dict]) -> str:
    colors = sorted({edge_color(edge) for edge in edges} or {EDGE_PALETTE["sync"]})
    parts: list[str] = []
    for color in colors:
        marker_id = marker_id_for_color(color)
        safe_color = escape(color)
        parts.append(
            f'<marker id="{marker_id}" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">'
            f'<polygon points="0 0, 12 4, 0 8" fill="{safe_color}" />'
            "</marker>"
        )
    return "".join(parts)


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
    if current_dir.parent.name == "diagrams":
        return "../../index.html"
    if len(current_dir.parts) >= 2 and current_dir.parent.name == "nodes":
        return "../../index.html"
    return None


def display_units(text: str) -> int:
    units = 0
    for char in text:
        units += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return max(units, 1)


def child_node_ids(diagram: dict) -> set[str]:
    return {str(child["node_id"]) for child in diagram.get("children", []) if child.get("node_id")}


def node_has_link_badge(node: dict, linked_node_ids: set[str]) -> bool:
    return str(node["id"]) in linked_node_ids or bool(node.get("badge"))


def default_node_width(node: dict) -> float:
    texts = [str(node.get("label", node["id"]))]
    texts.extend(str(item) for item in node.get("lines", [])[:4])
    if node.get("badge"):
        texts.append(str(node["badge"]))
    max_units = max(display_units(item) for item in texts if item)
    return min(max(DEFAULT_NODE_WIDTH, max_units * 7.2 + 44.0), 320.0)


def default_node_height(node: dict, has_badge: bool) -> float:
    line_count = min(len(node.get("lines", [])[:4]), 4)
    last_line_y = 49.0 + max(line_count - 1, 0) * 17.0 if line_count else 36.0
    bottom_room = 26.0 if has_badge else 14.0
    return max(DEFAULT_NODE_HEIGHT, last_line_y + bottom_room)


def normalize_node_sizes(diagram: dict, nodes: list[dict]) -> None:
    linked_node_ids = child_node_ids(diagram)
    for node in nodes:
        if "w" not in node:
            node["w"] = default_node_width(node)
        if "h" not in node:
            node["h"] = default_node_height(node, node_has_link_badge(node, linked_node_ids))


def node_centers(nodes: list[dict]) -> dict[str, tuple[float, float]]:
    centers: dict[str, tuple[float, float]] = {}
    for node in nodes:
        centers[str(node["id"])] = (
            float(node["x"]) + float(node.get("w", DEFAULT_NODE_WIDTH)) / 2.0,
            float(node["y"]) + float(node.get("h", DEFAULT_NODE_HEIGHT)) / 2.0,
        )
    return centers


def node_boxes(nodes: list[dict]) -> dict[str, dict[str, float]]:
    boxes: dict[str, dict[str, float]] = {}
    for node in nodes:
        boxes[str(node["id"])] = {
            "x": float(node["x"]),
            "y": float(node["y"]),
            "w": float(node.get("w", DEFAULT_NODE_WIDTH)),
            "h": float(node.get("h", DEFAULT_NODE_HEIGHT)),
        }
    return boxes


def canvas_size(diagram: dict, nodes: list[dict], groups: list[dict]) -> tuple[int, int]:
    viewport = diagram.get("viewport", {})
    min_width = int(viewport.get("min_width", viewport.get("width", DEFAULT_VIEWPORT_WIDTH)))
    min_height = int(viewport.get("min_height", viewport.get("height", DEFAULT_VIEWPORT_HEIGHT)))
    padding = float(viewport.get("content_padding", viewport.get("padding", DEFAULT_CANVAS_PADDING)))
    boxes = [
        {
            "x": float(node["x"]),
            "y": float(node["y"]),
            "w": float(node.get("w", DEFAULT_NODE_WIDTH)),
            "h": float(node.get("h", DEFAULT_NODE_HEIGHT)),
        }
        for node in nodes
    ]
    boxes.extend(
        {
            "x": float(group["x"]),
            "y": float(group["y"]),
            "w": float(group["w"]),
            "h": float(group["h"]),
        }
        for group in groups
    )
    max_right = max(box["x"] + box["w"] for box in boxes)
    max_bottom = max(box["y"] + box["h"] for box in boxes)
    width = max(min_width, math.ceil(max_right + padding))
    height = max(min_height, math.ceil(max_bottom + padding))
    return width, height


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


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def anchor_point(
    box: dict[str, float],
    center: tuple[float, float],
    other_center: tuple[float, float],
) -> tuple[tuple[float, float], str]:
    dx = other_center[0] - center[0]
    dy = other_center[1] - center[1]
    clearance = min(20.0, box["w"] / 2.0, box["h"] / 2.0)
    if abs(dx) >= abs(dy):
        side = "right" if dx >= 0 else "left"
        x = box["x"] + box["w"] if side == "right" else box["x"]
        y = clamp(center[1] + dy * 0.12, box["y"] + clearance, box["y"] + box["h"] - clearance)
        return (x, y), side

    side = "bottom" if dy >= 0 else "top"
    x = clamp(center[0] + dx * 0.12, box["x"] + clearance, box["x"] + box["w"] - clearance)
    y = box["y"] + box["h"] if side == "bottom" else box["y"]
    return (x, y), side


def segment_label_geometry(
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float, float, float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    mid_x = (start[0] + end[0]) / 2.0
    mid_y = (start[1] + end[1]) / 2.0
    if abs(dx) >= abs(dy):
        return mid_x, mid_y, 0.0, -1.0, length
    return mid_x, mid_y, 1.0, 0.0, length


def orthogonal_edge_path(
    source: tuple[float, float],
    source_side: str,
    target: tuple[float, float],
    target_side: str,
) -> tuple[str, float, float, float, float, float]:
    horizontal_sides = {"left", "right"}
    vertical_sides = {"top", "bottom"}
    points: list[tuple[float, float]]
    if source_side in horizontal_sides and target_side in horizontal_sides:
        if abs(source[1] - target[1]) < 1.0:
            points = [source, target]
        else:
            mid_x = (source[0] + target[0]) / 2.0
            points = [source, (mid_x, source[1]), (mid_x, target[1]), target]
    elif source_side in vertical_sides and target_side in vertical_sides:
        if abs(source[0] - target[0]) < 1.0:
            points = [source, target]
        else:
            mid_y = (source[1] + target[1]) / 2.0
            points = [source, (source[0], mid_y), (target[0], mid_y), target]
    elif source_side in horizontal_sides:
        points = [source, (target[0], source[1]), target]
    else:
        points = [source, (source[0], target[1]), target]

    d = " ".join(
        f"{'M' if index == 0 else 'L'} {point[0]:.1f},{point[1]:.1f}"
        for index, point in enumerate(points)
    )
    segments = [
        segment_label_geometry(points[index], points[index + 1])
        for index in range(len(points) - 1)
    ]
    label_mid_x, label_mid_y, normal_x, normal_y, segment_len = max(segments, key=lambda item: item[4])
    return d, label_mid_x, label_mid_y, normal_x, normal_y, segment_len


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
        source, source_side = anchor_point(source_box, source_center, target_center)
        target, target_side = anchor_point(target_box, target_center, source_center)
        raw_color = edge_color(edge)
        color = escape(raw_color)
        marker_id = marker_id_for_color(raw_color)
        label = edge.get("label")
        path_d, mid_x, mid_y, normal_x, normal_y, edge_len = orthogonal_edge_path(
            source,
            source_side,
            target,
            target_side,
        )
        line_parts.append(
            f'<path class="edge edge-{index}" d="{path_d}" fill="none" stroke="{color}" stroke-width="1.6"'
            f'{edge_dash(edge)} marker-end="url(#{marker_id})" />'
        )
        if label:
            label_text = str(label)
            label_width = max(46.0, display_units(label_text) * 6.8 + 18.0)
            label_height = 24.0
            offset = 18.0 if edge_len >= label_width + 32.0 else 28.0
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


def layout_number(settings: dict, key: str) -> float:
    return float(settings.get(key, DEFAULT_LAYOUT[key]))


def node_index(nodes: list[dict]) -> dict[str, int]:
    return {str(node["id"]): index for index, node in enumerate(nodes)}


def sort_node_ids(node_ids: list[str], nodes_by_id: dict[str, dict], index_by_id: dict[str, int]) -> list[str]:
    def order_value(node_id: str) -> int:
        raw_order = nodes_by_id[node_id].get("order", index_by_id[node_id])
        try:
            return int(raw_order)
        except (TypeError, ValueError):
            return index_by_id[node_id]

    return sorted(
        node_ids,
        key=lambda node_id: (
            order_value(node_id),
            index_by_id[node_id],
        ),
    )


def node_group_id(node: dict) -> str | None:
    for key in ("group", "layer", "lane"):
        if node.get(key) is not None:
            return str(node[key])
    return None


def readable_group_label(group_id: str) -> str:
    return group_id.replace("-", " ").replace("_", " ").title()


def declared_group_columns(nodes: list[dict], diagram_groups: list[dict]) -> list[dict]:
    nodes_by_id = {str(node["id"]): node for node in nodes}
    index_by_id = node_index(nodes)
    used_node_ids: set[str] = set()
    columns: list[dict] = []
    declared_ids: set[str] = set()

    for index, group in enumerate(diagram_groups):
        group_id = str(group.get("id") or group.get("label") or f"group-{index + 1}")
        declared_ids.add(group_id)
        explicit_ids = group_node_ids(group)
        ids = explicit_ids
        if explicit_ids:
            ids = [node_id for node_id in ids if node_id in nodes_by_id and node_id not in used_node_ids]
            if any("order" in nodes_by_id[node_id] for node_id in ids):
                ids = sort_node_ids(ids, nodes_by_id, index_by_id)
        else:
            ids = [str(node["id"]) for node in nodes if node_group_id(node) == group_id]
            ids = [node_id for node_id in ids if node_id in nodes_by_id and node_id not in used_node_ids]
            ids = sort_node_ids(ids, nodes_by_id, index_by_id)
        if not ids:
            continue
        used_node_ids.update(ids)
        columns.append(
            {
                "id": group_id,
                "label": str(group.get("label", readable_group_label(group_id))),
                "kind": group.get("kind", "generic"),
                "node_ids": ids,
                "render": True,
            }
        )

    for node in nodes:
        group_id = node_group_id(node)
        node_id = str(node["id"])
        if not group_id or node_id in used_node_ids:
            continue
        existing = next((item for item in columns if item["id"] == group_id), None)
        if existing:
            existing["node_ids"].append(node_id)
        else:
            columns.append(
                {
                    "id": group_id,
                    "label": readable_group_label(group_id),
                    "kind": node.get("kind", "generic"),
                    "node_ids": [node_id],
                    "render": group_id in declared_ids or not diagram_groups,
                }
            )
        used_node_ids.add(node_id)

    remaining = [str(node["id"]) for node in nodes if str(node["id"]) not in used_node_ids]
    if remaining:
        columns.append(
            {
                "id": "ungrouped",
                "label": "Ungrouped",
                "kind": "generic",
                "node_ids": sort_node_ids(remaining, nodes_by_id, index_by_id),
                "render": False,
            }
        )
    return columns


def rank_columns(nodes: list[dict]) -> list[dict]:
    groups: dict[str, list[str]] = {}
    for node in nodes:
        rank = str(node.get("rank", 0))
        groups.setdefault(rank, []).append(str(node["id"]))
    nodes_by_id = {str(node["id"]): node for node in nodes}
    index_by_id = node_index(nodes)

    def rank_sort_key(raw_rank: str) -> tuple[int, int | str]:
        try:
            return (0, int(raw_rank))
        except ValueError:
            return (1, raw_rank)

    return [
        {
            "id": f"rank-{rank}",
            "label": "",
            "kind": "generic",
            "node_ids": sort_node_ids(node_ids, nodes_by_id, index_by_id),
            "render": False,
        }
        for rank, node_ids in sorted(groups.items(), key=lambda item: rank_sort_key(item[0]))
    ]


def topology_columns(nodes: list[dict], edges: list[dict]) -> list[dict]:
    node_ids = [str(node["id"]) for node in nodes]
    node_id_set = set(node_ids)
    adjacency = {node_id: [] for node_id in node_ids}
    indegree = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        source_id = str(edge["from"])
        target_id = str(edge["to"])
        if source_id not in node_id_set or target_id not in node_id_set:
            continue
        adjacency[source_id].append(target_id)
        indegree[target_id] += 1

    rank = {node_id: 0 for node_id in node_ids}
    queue = [node_id for node_id in node_ids if indegree[node_id] == 0]
    visited: set[str] = set()
    while queue:
        current = queue.pop(0)
        visited.add(current)
        for target_id in adjacency[current]:
            rank[target_id] = max(rank[target_id], rank[current] + 1)
            indegree[target_id] -= 1
            if indegree[target_id] == 0:
                queue.append(target_id)

    if len(visited) != len(node_ids):
        fallback_rank = max(rank.values()) if rank else 0
        for node_id in node_ids:
            if node_id not in visited:
                rank[node_id] = fallback_rank

    grouped: dict[int, list[str]] = {}
    for node_id in node_ids:
        grouped.setdefault(rank[node_id], []).append(node_id)

    nodes_by_id = {str(node["id"]): node for node in nodes}
    index_by_id = node_index(nodes)
    return [
        {
            "id": f"stage-{rank_id + 1}",
            "label": "",
            "kind": "generic",
            "node_ids": sort_node_ids(node_ids_for_rank, nodes_by_id, index_by_id),
            "render": False,
        }
        for rank_id, node_ids_for_rank in sorted(grouped.items(), key=lambda item: item[0])
    ]


def layout_columns(diagram: dict, nodes: list[dict]) -> list[dict]:
    diagram_groups = diagram.get("groups", [])
    has_node_groups = any(node_group_id(node) for node in nodes)
    if diagram_groups or has_node_groups:
        return declared_group_columns(nodes, diagram_groups)
    if any("rank" in node for node in nodes):
        return rank_columns(nodes)
    return topology_columns(nodes, diagram.get("edges", []))


def column_content_height(column: dict, nodes_by_id: dict[str, dict], node_gap: float) -> float:
    heights = [float(nodes_by_id[node_id].get("h", DEFAULT_NODE_HEIGHT)) for node_id in column["node_ids"]]
    return sum(heights) + node_gap * max(len(heights) - 1, 0)


def column_content_width(column: dict, nodes_by_id: dict[str, dict], node_gap: float) -> float:
    widths = [float(nodes_by_id[node_id].get("w", DEFAULT_NODE_WIDTH)) for node_id in column["node_ids"]]
    return sum(widths) + node_gap * max(len(widths) - 1, 0)


def apply_auto_layout(diagram: dict, nodes: list[dict]) -> list[dict]:
    settings = {**DEFAULT_LAYOUT, **diagram.get("layout", {})}
    direction = str(settings.get("direction", "lr")).lower()
    if direction in {"td", "down", "vertical"}:
        direction = "tb"
    if direction not in {"lr", "tb"}:
        direction = "lr"

    margin_x = layout_number(settings, "margin_x")
    margin_y = layout_number(settings, "margin_y")
    rank_gap = layout_number(settings, "rank_gap")
    node_gap = layout_number(settings, "node_gap")
    group_padding_x = layout_number(settings, "group_padding_x")
    group_padding_y = layout_number(settings, "group_padding_y")
    min_group_width = layout_number(settings, "min_group_width")

    nodes_by_id = {str(node["id"]): node for node in nodes}
    columns = layout_columns(diagram, nodes)
    groups: list[dict] = []

    if direction == "tb":
        row_widths = [
            max(column_content_width(column, nodes_by_id, node_gap) + group_padding_x * 2, min_group_width)
            for column in columns
        ]
        row_heights = [
            max(
                max(float(nodes_by_id[node_id].get("h", DEFAULT_NODE_HEIGHT)) for node_id in column["node_ids"])
                + group_padding_y * 2,
                DEFAULT_NODE_HEIGHT + group_padding_y * 2,
            )
            for column in columns
        ]
        max_row_width = max(row_widths) if row_widths else min_group_width
        y = margin_y
        for column, row_height in zip(columns, row_heights):
            content_width = column_content_width(column, nodes_by_id, node_gap)
            x = margin_x + group_padding_x + max((max_row_width - group_padding_x * 2 - content_width) / 2.0, 0.0)
            for node_id in column["node_ids"]:
                node = nodes_by_id[node_id]
                node["x"] = x
                node["y"] = y + group_padding_y + (row_height - group_padding_y * 2 - float(node["h"])) / 2.0
                x += float(node["w"]) + node_gap
            groups.append(
                {
                    "id": column["id"],
                    "label": column["label"],
                    "kind": column["kind"],
                    "x": margin_x,
                    "y": y,
                    "w": max_row_width,
                    "h": row_height,
                    "render": column.get("render", False),
                }
            )
            y += row_height + rank_gap
        return [group for group in groups if group.get("render")]

    column_widths = [
        max(
            max(float(nodes_by_id[node_id].get("w", DEFAULT_NODE_WIDTH)) for node_id in column["node_ids"])
            + group_padding_x * 2,
            min_group_width,
        )
        for column in columns
    ]
    column_heights = [column_content_height(column, nodes_by_id, node_gap) + group_padding_y * 2 for column in columns]
    max_column_height = max(column_heights) if column_heights else DEFAULT_VIEWPORT_HEIGHT
    x = margin_x
    for column, column_width in zip(columns, column_widths):
        content_height = column_content_height(column, nodes_by_id, node_gap)
        y = margin_y + group_padding_y + max((max_column_height - group_padding_y * 2 - content_height) / 2.0, 0.0)
        for node_id in column["node_ids"]:
            node = nodes_by_id[node_id]
            node["x"] = x + group_padding_x + (column_width - group_padding_x * 2 - float(node["w"])) / 2.0
            node["y"] = y
            y += float(node["h"]) + node_gap
        groups.append(
            {
                "id": column["id"],
                "label": column["label"],
                "kind": column["kind"],
                "x": x,
                "y": margin_y,
                "w": column_width,
                "h": max_column_height,
                "render": column.get("render", False),
            }
        )
        x += column_width + rank_gap
    return [group for group in groups if group.get("render")]


def manual_group_boxes(diagram: dict, nodes: list[dict]) -> list[dict]:
    columns = declared_group_columns(nodes, diagram.get("groups", []))
    nodes_by_id = {str(node["id"]): node for node in nodes}
    groups: list[dict] = []
    for column in columns:
        if not column.get("render"):
            continue
        boxes = [
            {
                "x": float(nodes_by_id[node_id]["x"]),
                "y": float(nodes_by_id[node_id]["y"]),
                "w": float(nodes_by_id[node_id].get("w", DEFAULT_NODE_WIDTH)),
                "h": float(nodes_by_id[node_id].get("h", DEFAULT_NODE_HEIGHT)),
            }
            for node_id in column["node_ids"]
        ]
        min_x = min(box["x"] for box in boxes)
        min_y = min(box["y"] for box in boxes)
        max_right = max(box["x"] + box["w"] for box in boxes)
        max_bottom = max(box["y"] + box["h"] for box in boxes)
        groups.append(
            {
                "id": column["id"],
                "label": column["label"],
                "kind": column["kind"],
                "x": min_x - 22.0,
                "y": min_y - 40.0,
                "w": max_right - min_x + 44.0,
                "h": max_bottom - min_y + 62.0,
                "render": True,
            }
        )
    return groups


def prepare_diagram(diagram: dict) -> tuple[list[dict], list[dict]]:
    nodes = diagram["nodes"]
    normalize_node_sizes(diagram, nodes)
    mode = str(diagram.get("layout", {}).get("mode", "")).lower()
    all_positioned = all("x" in node and "y" in node for node in nodes)
    if mode in {"manual", "fixed"} and not all_positioned:
        raise SystemExit("invalid diagram: layout.mode=manual requires x/y on every node")
    if mode in {"auto", "semantic", "layered"} or not all_positioned:
        return nodes, apply_auto_layout(diagram, nodes)
    return nodes, manual_group_boxes(diagram, nodes)


def render_groups(groups: list[dict]) -> str:
    parts: list[str] = []
    for group in groups:
        fill, stroke = palette_for(group.get("kind"))
        label = escape(str(group.get("label", group.get("id", ""))))
        x = float(group["x"])
        y = float(group["y"])
        w = float(group["w"])
        h = float(group["h"])
        parts.append(
            '<g class="group-layer">'
            f'<rect class="group-box" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="16" fill="{fill}" stroke="{stroke}" stroke-width="1.2" />'
            f'<text class="group-label" x="{x + 16.0:.1f}" y="{y + 24.0:.1f}">{label}</text>'
            '</g>'
        )
    return "\n".join(parts)


def render_node(node: dict, href: str | None) -> str:
    x = float(node["x"])
    y = float(node["y"])
    w = float(node.get("w", DEFAULT_NODE_WIDTH))
    h = float(node.get("h", DEFAULT_NODE_HEIGHT))
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


def catalog_order(item: dict) -> tuple[int, str, str]:
    raw_order = item.get("order", 100000)
    try:
        order = int(raw_order)
    except (TypeError, ValueError):
        order = 100000
    return order, str(item.get("title", "")).lower(), catalog_id(item)


def render_item_chips(item: dict) -> str:
    chips = []
    for key in ("type", "view", "status"):
        value = str(item.get(key, "")).strip()
        if value:
            chips.append(f'<span class="chip">{escape(value)}</span>')
    for tag in item.get("tags", [])[:4]:
        chips.append(f'<span class="chip is-muted">{escape(str(tag))}</span>')
    return "".join(chips)


def render_cross_links(item: dict, items_by_id: dict[str, dict]) -> str:
    links = item.get("links", [])
    if not links:
        return ""
    parts: list[str] = []
    for link_id in links:
        linked = items_by_id.get(str(link_id))
        if not linked:
            continue
        parts.append(
            f'<a class="xref" href="{escape(str(linked["href"]))}">{escape(str(linked.get("title", link_id)))}</a>'
        )
    if not parts:
        return ""
    return f'<div class="xrefs"><span>Related</span>{"".join(parts)}</div>'


def render_portal_tree_item(
    item: dict,
    children_by_parent: dict[str, list[dict]],
    items_by_id: dict[str, dict],
    depth: int,
) -> str:
    diagram_id = catalog_id(item)
    children = sorted(children_by_parent.get(diagram_id, []), key=catalog_order)
    child_html = ""
    if children:
        child_items = [
            render_portal_tree_item(child, children_by_parent, items_by_id, depth + 1)
            for child in children
        ]
        child_html = f'<ol class="diagram-tree depth-{depth + 1}">{"".join(child_items)}</ol>'
    summary = str(item.get("summary", "")).strip()
    summary_html = f'<p>{escape(summary)}</p>' if summary else ""
    return (
        '<li class="tree-item">'
        '<article class="diagram-card">'
        f'<a class="diagram-title" href="{escape(str(item["href"]))}">{escape(str(item.get("title", diagram_id)))}</a>'
        f'<div class="diagram-meta">{render_item_chips(item)}</div>'
        f'{summary_html}'
        f'{render_cross_links(item, items_by_id)}'
        '</article>'
        f'{child_html}'
        '</li>'
    )


def render_portal_cards(items: list[dict], items_by_id: dict[str, dict]) -> str:
    parts: list[str] = []
    for item in sorted(items, key=catalog_order):
        diagram_id = catalog_id(item)
        summary = str(item.get("summary", "")).strip()
        summary_html = f'<p>{escape(summary)}</p>' if summary else ""
        parts.append(
            '<article class="standalone-card">'
            f'<a class="diagram-title" href="{escape(str(item["href"]))}">{escape(str(item.get("title", diagram_id)))}</a>'
            f'<div class="diagram-meta">{render_item_chips(item)}</div>'
            f'{summary_html}'
            f'{render_cross_links(item, items_by_id)}'
            '</article>'
        )
    return "".join(parts)


def render_portal(catalog_path: Path) -> Path:
    catalog = load_catalog(catalog_path)
    root = catalog_path.parent.resolve()
    diagrams = catalog_diagrams(catalog, catalog_path)
    items_by_id = {catalog_id(item): item for item in diagrams}
    children_by_parent: dict[str, list[dict]] = {}
    for item in diagrams:
        parent_id = str(item.get("parent_id", "")).strip()
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(item)

    roots = [item for item in diagrams if not str(item.get("parent_id", "")).strip()]
    tree_roots = [item for item in roots if catalog_id(item) in children_by_parent]
    standalone = [item for item in roots if catalog_id(item) not in children_by_parent]
    tree_html = "".join(
        render_portal_tree_item(item, children_by_parent, items_by_id, 0)
        for item in sorted(tree_roots, key=catalog_order)
    )
    standalone_html = render_portal_cards(standalone, items_by_id)

    site = catalog.get("site", {}) if isinstance(catalog.get("site", {}), dict) else {}
    title = str(site.get("title", "Project Architecture"))
    summary = str(site.get("summary", "Static architecture documentation."))
    diagram_count = len(diagrams)
    top_level_count = len(roots)
    child_count = diagram_count - top_level_count
    empty_tree = '<p class="empty">No related diagram groups yet.</p>' if not tree_html else f'<ol class="diagram-tree">{tree_html}</ol>'
    empty_standalone = '<p class="empty">No standalone diagrams yet.</p>' if not standalone_html else f'<div class="standalone-grid">{standalone_html}</div>'
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #06101d;
      --panel: rgba(9, 17, 31, 0.78);
      --panel-border: rgba(76, 113, 149, 0.35);
      --text: #e6edf7;
      --muted: #8ea6c1;
      --accent: #7dd3fc;
      --card-bg: rgba(10, 18, 34, 0.72);
    }}

    * {{ box-sizing: border-box; }}

    html,
    body {{
      margin: 0;
      min-height: 100%;
      background: linear-gradient(180deg, #08111e 0%, #040913 100%);
      color: var(--text);
      font-family: {FONT_STACK};
    }}

    body {{ padding: 28px; }}

    .page {{
      max-width: 1180px;
      margin: 0 auto;
      display: grid;
      gap: 22px;
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 22px;
      align-items: end;
      padding-bottom: 8px;
    }}

    .eyebrow {{
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0;
      margin-bottom: 10px;
    }}

    h1 {{
      margin: 0;
      font-size: 36px;
      line-height: 1.12;
    }}

    .summary {{
      margin: 12px 0 0;
      max-width: 780px;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.65;
    }}

    .stats {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}

    .stat {{
      min-width: 110px;
      padding: 12px 14px;
      border: 1px solid var(--panel-border);
      border-radius: 8px;
      background: rgba(8, 16, 30, 0.72);
    }}

    .stat strong {{
      display: block;
      font-size: 22px;
      line-height: 1.1;
    }}

    .stat span {{
      display: block;
      margin-top: 5px;
      color: var(--muted);
      font-size: 12px;
    }}

    .section {{
      border: 1px solid var(--panel-border);
      border-radius: 10px;
      background: var(--panel);
      padding: 18px;
    }}

    .section h2 {{
      margin: 0 0 14px;
      font-size: 18px;
      line-height: 1.25;
    }}

    .diagram-tree {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 12px;
    }}

    .diagram-tree .diagram-tree {{
      margin-top: 12px;
      padding-left: 24px;
      border-left: 1px solid rgba(125, 211, 252, 0.2);
    }}

    .tree-item {{
      display: grid;
      gap: 12px;
    }}

    .diagram-card,
    .standalone-card {{
      border: 1px solid rgba(106, 159, 211, 0.18);
      border-radius: 8px;
      background: var(--card-bg);
      padding: 15px;
    }}

    .diagram-title {{
      color: #f8fbff;
      text-decoration: none;
      font-size: 16px;
      font-weight: 800;
      line-height: 1.3;
    }}

    .diagram-title:hover,
    .diagram-title:focus {{
      color: var(--accent);
    }}

    .diagram-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
      margin-top: 10px;
    }}

    .chip {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 9px;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.13);
      border: 1px solid rgba(125, 211, 252, 0.22);
      color: #cfe5f7;
      font-size: 12px;
      line-height: 1.2;
    }}

    .chip.is-muted {{
      background: rgba(148, 163, 184, 0.12);
      border-color: rgba(148, 163, 184, 0.22);
      color: var(--muted);
    }}

    .diagram-card p,
    .standalone-card p,
    .empty {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
    }}

    .standalone-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 12px;
    }}

    .xrefs {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
      color: #6f86a2;
      font-size: 12px;
    }}

    .xref {{
      color: var(--accent);
      text-decoration: none;
    }}

    .footer {{
      margin: 0;
      color: #6f86a2;
      font-size: 12px;
      text-align: center;
    }}

    @media (max-width: 760px) {{
      body {{ padding: 16px; }}

      .hero {{
        grid-template-columns: 1fr;
        align-items: start;
      }}

      .stats {{
        justify-content: flex-start;
      }}

      h1 {{
        font-size: 30px;
      }}

      .diagram-tree .diagram-tree {{
        padding-left: 14px;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <div>
        <div class="eyebrow">Architecture Portal</div>
        <h1>{escape(title)}</h1>
        <p class="summary">{escape(summary)}</p>
      </div>
      <div class="stats">
        <div class="stat"><strong>{diagram_count}</strong><span>Diagrams</span></div>
        <div class="stat"><strong>{top_level_count}</strong><span>Top Level</span></div>
        <div class="stat"><strong>{child_count}</strong><span>Related</span></div>
      </div>
    </header>

    <section class="section">
      <h2>Related Diagrams</h2>
      {empty_tree}
    </section>

    <section class="section">
      <h2>Standalone Diagrams</h2>
      {empty_standalone}
    </section>

    <p class="footer">{escape(str(catalog_path.relative_to(Path.cwd()))) if catalog_path.is_relative_to(Path.cwd()) else escape(str(catalog_path))}</p>
  </main>
</body>
</html>
"""
    output_path = root / "index.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


def load_mermaid_meta(mmd_path: Path) -> dict:
    meta_path = mmd_path.with_name("diagram.meta.json")
    if not meta_path.exists():
        return {}
    data = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"invalid mermaid meta: root must be an object in {meta_path}")
    return data


def render_mermaid_diagram(mmd_path: Path) -> Path:
    source = mmd_path.read_text(encoding="utf-8").strip()
    if not source:
        raise SystemExit(f"invalid mermaid diagram: source is empty in {mmd_path}")
    meta = load_mermaid_meta(mmd_path)
    title = str(meta.get("title", mmd_path.parent.name.replace("-", " ").title()))
    summary = str(meta.get("summary", ""))
    breadcrumb_html = render_breadcrumb(title, parent_href(mmd_path))
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #06101d;
      --panel: rgba(9, 17, 31, 0.78);
      --panel-border: rgba(76, 113, 149, 0.35);
      --text: #e6edf7;
      --muted: #8ea6c1;
      --accent: #7dd3fc;
    }}

    * {{ box-sizing: border-box; }}

    html,
    body {{
      margin: 0;
      min-height: 100%;
      background: linear-gradient(180deg, #08111e 0%, #040913 100%);
      color: var(--text);
      font-family: {FONT_STACK};
    }}

    body {{ padding: 24px; }}

    .page {{
      max-width: 1440px;
      margin: 0 auto;
    }}

    .hero {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 20px;
    }}

    .eyebrow {{
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 10px;
    }}

    h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.12;
    }}

    .subtitle {{
      margin: 10px 0 0;
      color: var(--muted);
      max-width: 860px;
      line-height: 1.6;
      font-size: 15px;
    }}

    .breadcrumb {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(7, 14, 25, 0.7);
      border: 1px solid rgba(125, 211, 252, 0.18);
      font-size: 13px;
      color: var(--muted);
    }}

    .breadcrumb a {{
      color: var(--accent);
      text-decoration: none;
    }}

    .panel {{
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 10px;
      padding: 20px;
      overflow: auto;
      min-height: 420px;
    }}

    .mermaid {{
      min-width: 900px;
    }}

    .footer {{
      margin-top: 18px;
      color: #6f86a2;
      font-size: 12px;
      text-align: center;
    }}

    @media (max-width: 720px) {{
      body {{ padding: 16px; }}
      .hero {{
        align-items: flex-start;
        flex-direction: column;
      }}
      h1 {{ font-size: 28px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div>
        <div class="eyebrow">Mermaid Reference</div>
        <h1>{escape(title)}</h1>
        <p class="subtitle">{escape(summary)}</p>
      </div>
      {breadcrumb_html}
    </section>
    <section class="panel">
      <pre class="mermaid">
{escape(source)}
      </pre>
    </section>
    <p class="footer">{escape(str(mmd_path.relative_to(Path.cwd()))) if mmd_path.is_relative_to(Path.cwd()) else escape(str(mmd_path))}</p>
  </main>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, theme: "dark", securityLevel: "strict" }});
  </script>
</body>
</html>
"""
    output_path = mmd_path.with_name("index.html")
    output_path.write_text(html, encoding="utf-8")
    return output_path


def check_mermaid_diagram(mmd_path: Path) -> Path:
    source = mmd_path.read_text(encoding="utf-8").strip()
    if not source:
        raise SystemExit(f"invalid mermaid diagram: source is empty in {mmd_path}")
    load_mermaid_meta(mmd_path)
    return mmd_path


def build_svg(diagram: dict, diagram_path: Path) -> str:
    children = diagram.get("children", [])
    hrefs = child_href_map(children)
    nodes, groups = prepare_diagram(diagram)
    width, height = canvas_size(diagram, nodes, groups)
    centers = node_centers(nodes)
    boxes = node_boxes(nodes)
    edges = diagram.get("edges", [])
    edge_lines_html, edge_labels_html = render_edge_layers(edges, centers, boxes, width, height)
    edge_markers = render_edge_markers(edges)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(str(diagram.get("title", "Architecture")))}">'
        "<defs>"
        f"{edge_markers}"
        '<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
        '<path d="M 40 0 L 0 0 0 40" fill="none" stroke="#15304b" stroke-width="0.8" opacity="0.55" />'
        "</pattern>"
        "</defs>"
        '<rect width="100%" height="100%" fill="url(#grid)" />'
        f"{render_groups(groups)}"
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


def check_diagram(diagram_path: Path) -> Path:
    diagram = load_diagram(diagram_path)
    build_svg(diagram, diagram_path)
    return diagram_path


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


def check_recursive(diagram_path: Path, seen: set[Path]) -> list[Path]:
    diagram_path = diagram_path.resolve()
    if diagram_path in seen:
        return []
    seen.add(diagram_path)
    outputs = [check_diagram(diagram_path)]
    diagram = load_diagram(diagram_path)
    for child in diagram.get("children", []):
        child_path = child.get("path")
        if not child_path:
            continue
        child_diagram = (diagram_path.parent / child_path / "diagram.arch.json").resolve()
        if not child_diagram.exists():
            raise SystemExit(f"missing child diagram for {diagram_path}: {child_diagram}")
        outputs.extend(check_recursive(child_diagram, seen))
    return outputs


def render_catalog_sources(catalog_path: Path, template_path: Path) -> list[Path]:
    catalog = load_catalog(catalog_path)
    root = catalog_path.parent.resolve()
    outputs: list[Path] = []
    for item in sorted(catalog_diagrams(catalog, catalog_path), key=catalog_order):
        source = source_for_catalog_item(root, item)
        if not source:
            continue
        source_kind, source_path = source
        if source_kind == "arch":
            outputs.append(render_diagram(source_path, template_path))
        elif source_kind == "mermaid":
            outputs.append(render_mermaid_diagram(source_path))
    return outputs


def check_catalog_sources(catalog_path: Path) -> list[Path]:
    catalog = load_catalog(catalog_path)
    root = catalog_path.parent.resolve()
    outputs: list[Path] = [catalog_path]
    for item in sorted(catalog_diagrams(catalog, catalog_path), key=catalog_order):
        source = source_for_catalog_item(root, item)
        if not source:
            target = catalog_href_target(root, item)
            outputs.append(target)
            continue
        source_kind, source_path = source
        if source_kind == "arch":
            outputs.append(check_diagram(source_path))
        elif source_kind == "mermaid":
            outputs.append(check_mermaid_diagram(source_path))
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render arch sources into static HTML files.")
    parser.add_argument("diagram", help="catalog.json, arch root, diagram.arch.json, or directory that contains it")
    parser.add_argument("--recursive", action="store_true", help="render child diagrams or catalog diagrams recursively")
    parser.add_argument("--check", action="store_true", help="validate sources without writing index.html")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = resolve_input_path(args.diagram)
    if not input_path.exists():
        print(f"missing input: {input_path}", file=sys.stderr)
        return 2
    template_path = Path(__file__).resolve().parent.parent / "templates" / "arch" / "page.html.tmpl"

    if is_catalog_path(input_path):
        if args.check:
            if args.recursive:
                outputs = check_catalog_sources(input_path)
            else:
                load_catalog(input_path)
                outputs = [input_path]
        else:
            outputs = []
            if args.recursive:
                outputs.extend(render_catalog_sources(input_path, template_path))
            outputs.append(render_portal(input_path))
    elif input_path.name == "diagram.mmd":
        outputs = [check_mermaid_diagram(input_path)] if args.check else [render_mermaid_diagram(input_path)]
    elif args.check:
        outputs = check_recursive(input_path, set()) if args.recursive else [check_diagram(input_path)]
    else:
        outputs = (
            render_recursive(input_path, template_path, set())
            if args.recursive
            else [render_diagram(input_path, template_path)]
        )
    for output in outputs:
        print(f"ok {output}" if args.check else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
