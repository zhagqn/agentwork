#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


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


def resolve_target(raw: str) -> tuple[Path, list[Path] | None]:
    path = Path(raw).resolve()
    if path.is_dir():
        if (path / "catalog.json").exists():
            return path, None
        if is_item_dir(path):
            return item_dir_root(path), [path / "diagram.mmd"]
        raise SystemExit(f"invalid input: '{raw}' is neither arch root nor item directory")
    if path.name == "catalog.json" and path.is_file():
        return path.parent, None
    if path.name == "diagram.mmd" and path.is_file() and is_item_dir(path.parent):
        return item_dir_root(path.parent), [path]
    raise SystemExit(f"invalid input: '{raw}' is not supported")


def detect_chrome() -> str | None:
    env_value = os.environ.get("ARCH_MERMAID_CHROME")
    if env_value:
        return env_value

    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        resolved = shutil.which(command)
        if resolved:
            return resolved
    return None


def build_base_command() -> list[str]:
    mmdc = shutil.which("mmdc")
    if mmdc:
        return [mmdc]
    return ["npx", "-y", "@mermaid-js/mermaid-cli"]


def export_svg(
    source_path: Path,
    output_path: Path,
    theme: str | None,
    background: str,
    puppeteer_config: Path | None,
) -> None:
    command = build_base_command()
    command.extend(["-i", str(source_path), "-o", str(output_path), "-b", background])
    if theme:
        command.extend(["-t", theme])
    if puppeteer_config:
        command.extend(["-p", str(puppeteer_config)])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise SystemExit(f"mermaid export failed: {source_path}\n{detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export diagram.mmd files to diagram.svg with Mermaid CLI")
    parser.add_argument("target", help="arch root, catalog.json, item directory, or diagram.mmd file")
    parser.add_argument(
        "--theme",
        choices=("default", "forest", "dark", "neutral"),
        help="override Mermaid CLI theme; omitted means use Mermaid defaults/source init",
    )
    parser.add_argument("--background", default="transparent", help="background color for generated SVG")
    parser.add_argument("--puppeteer-config", help="existing puppeteer config file for Mermaid CLI")
    args = parser.parse_args()

    root, selected_sources = resolve_target(args.target)
    source_paths = selected_sources or sorted((root / "content").glob("**/diagram.mmd"))
    if not source_paths:
        raise SystemExit(f"no Mermaid sources found under {root}")

    temp_config_path: Path | None = None
    puppeteer_config = Path(args.puppeteer_config).resolve() if args.puppeteer_config else None
    if puppeteer_config is None:
        chrome_path = detect_chrome()
        if chrome_path:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as handle:
                json.dump(
                    {
                        "executablePath": chrome_path,
                        "args": ["--no-sandbox", "--disable-setuid-sandbox"],
                    },
                    handle,
                )
                temp_config_path = Path(handle.name)
            puppeteer_config = temp_config_path

    try:
        for source_path in source_paths:
            output_path = source_path.with_name("diagram.svg")
            export_svg(source_path, output_path, args.theme, args.background, puppeteer_config)
            print(f"arch_export_mermaid:WROTE:{output_path}")
    finally:
        if temp_config_path and temp_config_path.exists():
            temp_config_path.unlink()


if __name__ == "__main__":
    main()
