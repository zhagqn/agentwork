from __future__ import annotations

from pathlib import Path


TEXT_SUFFIXES = {'.ts', '.tsx', '.md'}


def _read_text_tree(root: Path) -> str:
    contents: list[str] = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            contents.append(path.read_text(encoding='utf-8'))
    return '\n'.join(contents)


def find_text_file_with_all(project: Path, root_rel: str, texts: list[str], failures: list[str], label: str) -> Path | None:
    root = project / root_rel
    if not root.exists():
        failures.append(f'missing_artifact_root:{root_rel}')
        return None
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding='utf-8')
        if all(text in content for text in texts):
            return path
    failures.append(f'missing_artifact:{label}:{root_rel}:{",".join(texts)}')
    return None


def check_text_collection_with_all(
    project: Path,
    root_rels: list[str],
    texts: list[str],
    failures: list[str],
    label: str,
) -> bool:
    contents: list[str] = []
    for root_rel in root_rels:
        root = project / root_rel
        if not root.exists():
            failures.append(f'missing_artifact_root:{root_rel}')
            continue
        if root.is_file():
            if root.suffix in TEXT_SUFFIXES:
                contents.append(root.read_text(encoding='utf-8'))
            continue
        contents.append(_read_text_tree(root))

    joined = '\n'.join(contents)
    missing = [text for text in texts if text not in joined]
    if not missing:
        return True
    failures.append(f'missing_artifact:{label}:{",".join(root_rels)}:{",".join(missing)}')
    return False


def find_text_file_with_required_and_any(
    project: Path,
    root_rel: str,
    required_texts: list[str],
    any_texts: list[str],
    failures: list[str],
    label: str,
) -> Path | None:
    root = project / root_rel
    if not root.exists():
        failures.append(f'missing_artifact_root:{root_rel}')
        return None
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding='utf-8')
        if all(text in content for text in required_texts) and any(text in content for text in any_texts):
            return path
    failures.append(f'missing_artifact:{label}:{root_rel}:{",".join(required_texts)}+any({",".join(any_texts)})')
    return None


def check_text_tree_with_required_and_any_groups(
    project: Path,
    root_rel: str,
    required_texts: list[str],
    any_groups: list[list[str]],
    failures: list[str],
    label: str,
) -> bool:
    root = project / root_rel
    if not root.exists():
        failures.append(f'missing_artifact_root:{root_rel}')
        return False
    joined = _read_text_tree(root)
    missing_required = [text for text in required_texts if text not in joined]
    missing_groups = [
        group for group in any_groups if not any(text in joined for text in group)
    ]
    if not missing_required and not missing_groups:
        return True
    group_desc = '+'.join(f'any({",".join(group)})' for group in any_groups)
    failures.append(
        f'missing_artifact:{label}:{root_rel}:{",".join(required_texts)}+{group_desc}'
    )
    return False


def check_contains(path: Path, text: str, failures: list[str], label: str | None = None) -> None:
    if not path.exists():
        failures.append(f'missing:{path}')
        return
    if text not in path.read_text(encoding='utf-8'):
        failures.append(f'missing_text:{label or path}:{text}')
