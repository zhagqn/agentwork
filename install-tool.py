#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
TOOLS_ROOT = ROOT / '.agentwork' / 'tools'
REGISTRY = TOOLS_ROOT / 'registry.json'
COMMANDS = {'install', 'uninstall', 'list'}
REGISTRY_SCHEMA_VERSION = 1
ENV_KEY_FIELDS = {'name', 'required', 'description'}
ENV_NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
ENV_ASSIGNMENT = re.compile(r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$')


@dataclass(frozen=True)
class EnvKey:
    name: str
    required: bool
    description: str


@dataclass(frozen=True)
class ToolEntry:
    surface: str
    src: Path
    dst: Path


@dataclass(frozen=True)
class EnvPlan:
    path: Path
    before: bytes
    after: bytes
    statuses: tuple[tuple[str, str], ...]
    add_gitignore: bool = False


@dataclass(frozen=True)
class PathSnapshot:
    path: Path
    kind: str
    backup: Path | None


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f'invalid JSON: {path}: {exc}')
    if not isinstance(data, dict):
        fail(f'expected JSON object: {path}')
    return data


def load_env_keys(tool_name: str, manifest: dict) -> tuple[EnvKey, ...]:
    raw_keys = manifest.get('env_keys', [])
    if not isinstance(raw_keys, list):
        fail(f'{tool_name}: env_keys must be a list')

    result: list[EnvKey] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_keys):
        if not isinstance(raw, dict) or set(raw) != ENV_KEY_FIELDS:
            fail(f'{tool_name}: env_keys[{index}] must contain exactly name, required, description')
        name = raw['name']
        required = raw['required']
        description = raw['description']
        if not isinstance(name, str) or not ENV_NAME.fullmatch(name):
            fail(f'{tool_name}: invalid env key name at env_keys[{index}]')
        if not isinstance(required, bool):
            fail(f'{tool_name}: env_keys[{index}].required must be boolean')
        if not isinstance(description, str) or not description.strip():
            fail(f'{tool_name}: env_keys[{index}].description must be a non-empty string')
        if name in seen:
            fail(f'{tool_name}: duplicate env key: {name}')
        seen.add(name)
        result.append(EnvKey(name, required, description))
    return tuple(result)


def load_tools() -> tuple[dict, dict[str, dict]]:
    registry = load_json(REGISTRY)
    if registry.get('schema_version') != REGISTRY_SCHEMA_VERSION:
        fail(f'unsupported registry schema: {REGISTRY}')
    raw_tools = registry.get('tools')
    if not isinstance(raw_tools, list):
        fail('registry tools must be a list')

    tools: dict[str, dict] = {}
    managed_keys: dict[str, str] = {}
    for index, item in enumerate(raw_tools):
        if not isinstance(item, dict):
            fail(f'registry tools[{index}] must be an object')
        name = item.get('name')
        directory = item.get('dir')
        kind = item.get('kind')
        if not isinstance(name, str) or not name:
            fail(f'registry tools[{index}].name must be a non-empty string')
        if name in tools:
            fail(f'duplicate registry tool: {name}')
        if not isinstance(directory, str) or not directory or Path(directory).is_absolute() or '..' in Path(directory).parts:
            fail(f'{name}: invalid registry dir')
        if not isinstance(kind, list) or not kind or not all(isinstance(value, str) and value for value in kind):
            fail(f'{name}: registry kind must be a non-empty string list')

        tool_dir = TOOLS_ROOT / directory
        manifest = load_json(tool_dir / 'tool.json')
        if manifest.get('name') != name:
            fail(f'{name}: manifest name does not match registry')
        if manifest.get('kind') != kind:
            fail(f'{name}: manifest kind does not match registry')
        env_keys = load_env_keys(name, manifest)
        for env_key in env_keys:
            owner = managed_keys.get(env_key.name)
            if owner is not None:
                fail(f'env key {env_key.name} is managed by both {owner} and {name}')
            managed_keys[env_key.name] = name

        tools[name] = {
            **manifest,
            'dir': directory,
            'tool_dir': tool_dir,
            'env_keys': env_keys,
        }
    return registry, tools


def normalize_tool_names(raw_names: list[str]) -> list[str]:
    names: list[str] = []
    for item in raw_names:
        for part in item.split(','):
            name = part.strip()
            if name and name not in names:
                names.append(name)
    return names


def target_rel(target: Path, path: Path) -> str:
    try:
        return str(path.relative_to(target))
    except ValueError:
        return str(path)


def safe_relative_path(tool_name: str, field: str, value: object) -> Path:
    if not isinstance(value, str) or not value:
        fail(f'{tool_name}: {field} must be a non-empty string')
    path = Path(value)
    if path == Path('.'):
        fail(f'{tool_name}: {field} must name a child path')
    if path.is_absolute() or '..' in path.parts:
        fail(f'{tool_name}: {field} must stay inside its root: {value}')
    return path


def safe_target_path(project_root: Path, tool_name: str, target_path: Path) -> Path:
    target = project_root / target_path
    current = project_root
    for part in target_path.parts:
        current /= part
        if current.is_symlink():
            fail(f'{tool_name}: target path contains symlink: {target_path}')
    resolved = target.resolve(strict=False)
    if not resolved.is_relative_to(project_root):
        fail(f'{tool_name}: target escapes project root: {target_path}')
    return target


def build_tool_entries(
    project_root: Path,
    tool_name: str,
    tool: dict,
    seen_targets: set[Path],
) -> tuple[ToolEntry, ...]:
    raw_entries = tool.get('entries', [])
    if not isinstance(raw_entries, list) or not raw_entries:
        fail(f'{tool_name}: entries must be a non-empty list')

    tool_root = tool['tool_dir'].resolve()
    entries: list[ToolEntry] = []
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict) or set(raw) != {'surface', 'from', 'to'}:
            fail(f'{tool_name}: entries[{index}] must contain exactly surface, from, to')
        surface = raw['surface']
        if not isinstance(surface, str) or not surface:
            fail(f'{tool_name}: entries[{index}].surface must be a non-empty string')
        source_rel = safe_relative_path(tool_name, f'entries[{index}].from', raw['from'])
        target_path = safe_relative_path(tool_name, f'entries[{index}].to', raw['to'])

        src = (tool_root / source_rel).resolve()
        if not src.is_relative_to(tool_root) or not src.exists() or not (src.is_file() or src.is_dir()):
            fail(f'{tool_name}: source does not exist or is unsupported: {raw["from"]}')
        dst = safe_target_path(project_root, tool_name, target_path)
        conflict = next((seen for seen in seen_targets if dst.is_relative_to(seen) or seen.is_relative_to(dst)), None)
        if conflict is not None:
            fail(
                'overlapping install targets: '
                f'{target_rel(project_root, dst)} and {target_rel(project_root, conflict)}'
            )
        seen_targets.add(dst)

        if src.is_dir() and dst.exists() and (dst.is_symlink() or not dst.is_dir()):
            fail(f'target path is a file, expected directory: {dst}')
        if src.is_file() and dst.exists() and dst.is_dir():
            fail(f'target path is a directory, expected file: {dst}')
        entries.append(ToolEntry(surface, src, dst))
    return tuple(entries)


def atomic_write_bytes(
    path: Path,
    content: bytes,
    *,
    mode_source: Path | None = None,
) -> None:
    """Replace a managed file without following a destination hardlink."""
    path.parent.mkdir(parents=True, exist_ok=True)
    mode: int | None = None
    if mode_source is not None and mode_source.is_file() and not mode_source.is_symlink():
        mode = mode_source.stat().st_mode & 0o7777
    elif path.exists() and not path.is_symlink() and path.is_file():
        mode = path.stat().st_mode & 0o7777

    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f'.{path.name}.',
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_name = handle.name
            os.chmod(temp_name, mode if mode is not None else 0o644)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink()
            except FileNotFoundError:
                pass


def copy_entry(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        dst.mkdir(exist_ok=True)
        return 'dir'
    atomic_write_bytes(dst, src.read_bytes(), mode_source=src)
    return 'file'


def remove_entry(dst: Path) -> str:
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
        return 'file'
    if dst.is_dir():
        shutil.rmtree(dst)
        return 'dir'
    return 'missing'


def prune_empty_parents(path: Path, project_root: Path) -> None:
    current = path
    while current != project_root and current.exists():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def git_result(project_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ['git', '-C', str(project_root), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def is_git_worktree(project_root: Path) -> bool:
    if not project_root.is_dir():
        return False
    result = git_result(project_root, 'rev-parse', '--is-inside-work-tree')
    return result.returncode == 0 and result.stdout.strip() == b'true'


def is_env_tracked(project_root: Path) -> bool:
    return is_git_worktree(project_root) and git_result(
        project_root, 'ls-files', '--error-unmatch', '--', '.env'
    ).returncode == 0


def is_env_ignored(project_root: Path) -> bool:
    if is_git_worktree(project_root):
        return git_result(
            project_root, 'check-ignore', '--quiet', '--no-index', '--', '.env'
        ).returncode == 0

    gitignore = project_root / '.gitignore'
    if not gitignore.is_file() or gitignore.is_symlink():
        return False
    # 非 Git 项目不解释整套 ignore 规则；仅信任最后一条非空行的明确保护。
    # 无法证明时在末尾追加 .env，避免早先的规则被后续否定模式抵消。
    lines = [line for line in gitignore.read_bytes().splitlines() if line.strip()]
    return bool(lines) and lines[-1] == b'.env'


def line_body(line: bytes) -> str:
    try:
        return line.rstrip(b'\r\n').decode('utf-8')
    except UnicodeDecodeError as exc:
        fail(f'.env must be UTF-8: {exc}')


def newline_for(data: bytes) -> bytes:
    for line in data.splitlines(keepends=True):
        if line.endswith(b'\r\n'):
            return b'\r\n'
        if line.endswith(b'\n'):
            return b'\n'
        if line.endswith(b'\r'):
            return b'\r'
    return b'\n'


def assignment_info(data: bytes, keys: set[str]) -> tuple[list[bytes], dict[str, tuple[int, str]]]:
    try:
        data.decode('utf-8')
    except UnicodeDecodeError as exc:
        fail(f'.env must be UTF-8: {exc}')
    lines = data.splitlines(keepends=True)
    assignments: dict[str, tuple[int, str]] = {}
    for index, line in enumerate(lines):
        match = ENV_ASSIGNMENT.fullmatch(line_body(line))
        if match is None or match.group(1) not in keys:
            continue
        name = match.group(1)
        if name in assignments:
            fail(f'.env contains duplicate key: {name}')
        assignments[name] = (index, match.group(2))
    return lines, assignments


def marker_for(tool_name: str) -> str:
    return f'# agentwork:env:{tool_name}'


def no_final_newline_marker(tool_name: str, key_name: str) -> str:
    return f'# agentwork:env-format:{tool_name}:{key_name}:no-final-newline'


def managed_assignment(
    lines: list[bytes],
    assignment_index: int,
    tool_name: str,
    key_name: str,
) -> tuple[int, int | None] | None:
    if assignment_index < 1:
        return None
    previous = line_body(lines[assignment_index - 1])
    if previous == marker_for(tool_name):
        return assignment_index - 1, None
    if previous == no_final_newline_marker(tool_name, key_name) and assignment_index >= 2:
        if line_body(lines[assignment_index - 2]) == marker_for(tool_name):
            return assignment_index - 2, assignment_index - 1
    return None


def preflight_env_path(project_root: Path, env_keys: list[tuple[str, EnvKey]]) -> tuple[Path, bytes]:
    env_path = project_root / '.env'
    if not env_keys:
        return env_path, b''
    if env_path.is_symlink() or (env_path.exists() and not env_path.is_file()):
        fail('.env must be a regular project-root file')
    if is_env_tracked(project_root):
        fail('refusing to manage tracked project-root .env')
    before = env_path.read_bytes() if env_path.exists() else b''
    assignment_info(before, {env_key.name for _, env_key in env_keys})
    return env_path, before


def prepare_install_env(project_root: Path, env_keys: list[tuple[str, EnvKey]]) -> EnvPlan:
    env_path, before = preflight_env_path(project_root, env_keys)
    if not env_keys:
        return EnvPlan(env_path, before, before, ())

    lines, assignments = assignment_info(before, {env_key.name for _, env_key in env_keys})
    after = before
    statuses: list[tuple[str, str]] = []
    newline = newline_for(before)
    for tool_name, env_key in env_keys:
        existing = assignments.get(env_key.name)
        if existing is not None:
            index, value = existing
            owned = managed_assignment(lines, index, tool_name, env_key.name) is not None
            state = 'empty' if not value.strip() else 'set'
            statuses.append((env_key.name, f'{"managed" if owned else "existing"}-{state}'))
            continue

        joined = bool(after) and not after.endswith((b'\n', b'\r'))
        if joined:
            after += newline
        block_lines = [marker_for(tool_name)]
        if joined:
            block_lines.append(no_final_newline_marker(tool_name, env_key.name))
        block_lines.append(f'{env_key.name}=')
        after += newline.join(line.encode('utf-8') for line in block_lines) + newline
        statuses.append((env_key.name, 'added-empty'))

    add_gitignore = not is_env_ignored(project_root)
    gitignore = project_root / '.gitignore'
    if add_gitignore and (gitignore.is_symlink() or (gitignore.exists() and not gitignore.is_file())):
        fail('.gitignore must be a regular project-root file')
    return EnvPlan(env_path, before, after, tuple(statuses), add_gitignore)


def strip_one_line_ending(line: bytes) -> bytes:
    if line.endswith(b'\r\n'):
        return line[:-2]
    if line.endswith((b'\n', b'\r')):
        return line[:-1]
    return line


def prepare_uninstall_env(project_root: Path, env_keys: list[tuple[str, EnvKey]]) -> EnvPlan:
    env_path, before = preflight_env_path(project_root, env_keys)
    if not env_keys or not env_path.exists():
        statuses = tuple((env_key.name, 'missing') for _, env_key in env_keys)
        return EnvPlan(env_path, before, before, statuses)

    lines, assignments = assignment_info(before, {env_key.name for _, env_key in env_keys})
    remove_indexes: set[int] = set()
    restore_candidates: list[int] = []
    statuses: list[tuple[str, str]] = []
    for tool_name, env_key in env_keys:
        existing = assignments.get(env_key.name)
        if existing is None:
            statuses.append((env_key.name, 'missing'))
            continue
        assignment_index, value = existing
        managed = managed_assignment(lines, assignment_index, tool_name, env_key.name)
        if managed is None:
            statuses.append((env_key.name, 'existing-preserved'))
            continue
        marker_index, format_index = managed
        remove_indexes.add(marker_index)
        if format_index is not None:
            remove_indexes.add(format_index)
        if value.strip():
            statuses.append((env_key.name, 'set-preserved'))
            continue
        remove_indexes.add(assignment_index)
        statuses.append((env_key.name, 'empty-removed'))
        if format_index is not None and marker_index > 0:
            restore_candidates.append(marker_index - 1)

    for candidate in restore_candidates:
        if not any(index > candidate and index not in remove_indexes for index in range(len(lines))):
            lines[candidate] = strip_one_line_ending(lines[candidate])
    after = b''.join(line for index, line in enumerate(lines) if index not in remove_indexes)
    return EnvPlan(env_path, before, after, tuple(statuses))


def append_gitignore_rule(project_root: Path) -> None:
    path = project_root / '.gitignore'
    before = path.read_bytes() if path.exists() else b''
    newline = newline_for(before)
    after = before
    if after and not after.endswith((b'\n', b'\r')):
        after += newline
    after += b'.env' + newline
    atomic_write_bytes(path, after)


def apply_env_plan(project_root: Path, plan: EnvPlan) -> None:
    if plan.add_gitignore:
        append_gitignore_rule(project_root)
        print('- [gitignore] .env')
    if plan.after != plan.before:
        atomic_write_bytes(plan.path, plan.after)
    for key_name, status in plan.statuses:
        print(f'- [env:{status}] {key_name}')


def snapshot_path(path: Path, backup: Path) -> PathSnapshot:
    if path.is_symlink():
        fail(f'refusing to snapshot symlink: {path}')
    if path.is_file():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        return PathSnapshot(path, 'file', backup)
    if path.is_dir():
        shutil.copytree(path, backup, symlinks=True)
        return PathSnapshot(path, 'dir', backup)
    if path.exists():
        fail(f'unsupported transaction path: {path}')
    return PathSnapshot(path, 'missing', None)


def restore_snapshot(snapshot: PathSnapshot) -> None:
    remove_entry(snapshot.path)
    if snapshot.kind == 'missing':
        return
    snapshot.path.parent.mkdir(parents=True, exist_ok=True)
    if snapshot.kind == 'file':
        atomic_write_bytes(
            snapshot.path,
            snapshot.backup.read_bytes(),
            mode_source=snapshot.backup,
        )
        return
    if snapshot.kind == 'dir':
        shutil.copytree(snapshot.backup, snapshot.path, symlinks=True)
        return
    raise RuntimeError(f'unknown snapshot kind: {snapshot.kind}')


def transaction_paths(
    grouped: list[tuple[str, tuple[ToolEntry, ...]]],
    env_plan: EnvPlan,
) -> tuple[Path, ...]:
    paths = [entry.dst for _, entries in grouped for entry in entries]
    if env_plan.after != env_plan.before:
        paths.append(env_plan.path)
    if env_plan.add_gitignore:
        paths.append(env_plan.path.parent / '.gitignore')
    return tuple(dict.fromkeys(paths))


def prepare_owned_changes(
    project_root: Path,
    action: str,
    grouped: list[tuple[str, tuple[ToolEntry, ...]]],
) -> tuple[list[tuple[str, tuple[ToolEntry, ...]]], dict[Path, bytes | None]]:
    """所有工具统一预检；manifest 路径本身不是所有权证据。"""
    planned: list[tuple[str, tuple[ToolEntry, ...]]] = []
    receipts: dict[Path, bytes | None] = {}
    for name, entries in grouped:
        receipt = safe_target_path(
            project_root, name,
            safe_relative_path(name, 'receipt', f'.agentwork/tool-receipts/{name}.json'),
        )
        previous: dict[str, str] = {}
        if receipt.exists():
            data = load_json(receipt)
            if set(data) != {'version', 'files'} or data['version'] != 1 or not isinstance(data['files'], dict):
                fail(f'{name}: invalid tool receipt: {receipt}')
            previous = data['files']
        owned: dict[str, Path] = {}
        for relative, digest in previous.items():
            rel = safe_relative_path(name, 'receipt file', relative)
            dst = safe_target_path(project_root, name, rel)
            # 退役路径只阻断 install：卸载必须仍能按旧收据清理，否则用户无路可退。
            if action == 'install' and not any(
                dst == entry.dst or (entry.src.is_dir() and dst.is_relative_to(entry.dst))
                for entry in entries
            ):
                fail(f'{name}: receipt path outside current manifest; reconcile manually: {relative}')
            if not isinstance(digest, str) or (digest != 'directory' and re.fullmatch(r'[0-9a-f]{64}', digest) is None):
                fail(f'{name}: invalid receipt digest: {relative}')
            matches = dst.is_dir() if digest == 'directory' else dst.is_file() and hashlib.sha256(dst.read_bytes()).hexdigest() == digest
            if dst.exists() and not matches:
                fail(f'{name}: ownership conflict (modified managed file): {relative}')
            owned[relative] = dst

        changes: list[ToolEntry] = []
        # 源已移除的文件暂不在升级时删除，保留记录供后续卸载核对。
        updated = dict(previous)
        if action == 'install':
            for entry in entries:
                sources = sorted(entry.src.rglob('*')) if entry.src.is_dir() and any(entry.src.iterdir()) else [entry.src]
                for src in sources:
                    relative_source = src.relative_to(entry.src) if entry.src.is_dir() else Path(src.name)
                    if '__pycache__' in relative_source.parts or src.suffix in {'.pyc', '.pyo'}:
                        continue
                    if src.is_symlink():
                        fail(f'{name}: unsupported source symlink: {src}')
                    if src.is_dir() and any(src.iterdir()):
                        continue
                    if not src.is_file() and not src.is_dir():
                        fail(f'{name}: unsupported source file: {src}')
                    dst = entry.dst / relative_source if entry.src.is_dir() else entry.dst
                    dst = safe_target_path(project_root, name, dst.relative_to(project_root))
                    relative = dst.relative_to(project_root).as_posix()
                    if src.is_dir() and dst.is_dir():
                        continue
                    if dst.exists() and relative not in owned:
                        fail(f'{name}: ownership conflict (unmanaged file): {relative}')
                    changes.append(ToolEntry(entry.surface, src, dst))
                    updated[relative] = 'directory' if src.is_dir() else hashlib.sha256(src.read_bytes()).hexdigest()
            receipts[receipt] = (json.dumps({'version': 1, 'files': updated}, indent=2, sort_keys=True) + '\n').encode()
        else:
            changes = [ToolEntry('receipt', dst, dst) for dst in owned.values()
                       if not dst.is_dir() or not any(dst.iterdir())]
            if receipt.exists():
                receipts[receipt] = None
        planned.append((name, tuple(changes)))
    return planned, receipts


def apply_receipts(receipts: dict[Path, bytes | None], project_root: Path) -> None:
    for path, content in receipts.items():
        if content is None:
            path.unlink()
            prune_empty_parents(path.parent, project_root)
        else:
            atomic_write_bytes(path, content)


def new_parent_paths(project_root: Path, paths: tuple[Path, ...]) -> tuple[Path, ...]:
    missing: set[Path] = set()
    if not project_root.exists():
        missing.add(project_root)
    for path in paths:
        if path == project_root or not path.is_relative_to(project_root):
            fail(f'transaction path must be below project root: {path}')
        current = path.parent
        while current != project_root:
            if not current.exists():
                missing.add(current)
            current = current.parent
    return tuple(sorted(missing, key=lambda item: len(item.parts), reverse=True))


def run_transaction(
    project_root: Path,
    paths: tuple[Path, ...],
    operation: Callable[[], None],
) -> None:
    new_parents = new_parent_paths(project_root, paths)
    with tempfile.TemporaryDirectory(prefix='agentwork-tool-rollback-') as temp:
        backup_root = Path(temp)
        try:
            snapshots = tuple(
                snapshot_path(path, backup_root / str(index))
                for index, path in enumerate(paths)
            )
        except (OSError, shutil.Error) as exc:
            fail(f'cannot prepare transaction backup: {exc}')

        try:
            operation()
        except (Exception, KeyboardInterrupt, SystemExit) as exc:
            rollback_errors: list[str] = []
            for snapshot in reversed(snapshots):
                try:
                    restore_snapshot(snapshot)
                except (Exception, KeyboardInterrupt, SystemExit) as rollback_exc:
                    rollback_errors.append(f'{snapshot.path}: {rollback_exc}')
            for path in new_parents:
                try:
                    path.rmdir()
                except FileNotFoundError:
                    pass
                except OSError:
                    if path.exists() and not any(path.iterdir()):
                        rollback_errors.append(f'{path}: could not remove restored empty directory')
            if rollback_errors:
                fail(f'transaction failed: {exc}; rollback incomplete: {"; ".join(rollback_errors)}')
            fail(f'transaction failed and rolled back: {exc}')


def apply_tool_changes(
    project_root: Path,
    action: str,
    grouped: list[tuple[str, tuple[ToolEntry, ...]]],
    env_plan: EnvPlan,
) -> None:
    if action == 'uninstall':
        print('== Uninstalling tools ==')
        for tool_name, entries in grouped:
            print(f'== Tool: {tool_name} ==')
            for entry in sorted(entries, key=lambda item: len(item.dst.parts), reverse=True):
                if entry.dst.is_dir():
                    entry.dst.rmdir()
                    removed_kind = 'dir'
                else:
                    removed_kind = remove_entry(entry.dst)
                if removed_kind == 'missing':
                    print(f'- [skip] {entry.surface}: {target_rel(project_root, entry.dst)} (missing)')
                    continue
                prune_empty_parents(entry.dst.parent, project_root)
                print(f'- [remove-{removed_kind}] {entry.surface}: {target_rel(project_root, entry.dst)}')
        apply_env_plan(project_root, env_plan)
        return

    project_root.mkdir(parents=True, exist_ok=True)
    print('== Installing tools ==')
    for tool_name, entries in grouped:
        print(f'== Tool: {tool_name} ==')
        for entry in entries:
            copied_kind = copy_entry(entry.src, entry.dst)
            print(f'- [{copied_kind}:{entry.surface}] {target_rel(project_root, entry.dst)}')
    apply_env_plan(project_root, env_plan)


def resolve_action(
    raw_args: list[str],
    install_flag: bool,
    uninstall_flag: bool,
    list_flag: bool,
) -> tuple[str, list[str]]:
    if list_flag:
        if raw_args:
            fail('list does not accept tool names')
        return 'list', []
    if install_flag:
        return 'install', raw_args
    if uninstall_flag:
        return 'uninstall', raw_args
    if not raw_args:
        fail('command is required: install, uninstall, list, or use -i/-u/-l')
    action = raw_args[0]
    if action not in COMMANDS:
        fail(f'unknown command: {raw_args[0]}')
    return action, raw_args[1:]


def main() -> int:
    parser = argparse.ArgumentParser(description='Manage optional tools from .agentwork/tools in a target project.')
    parser.add_argument('args', nargs='*', help='command + tool names; commands: install, uninstall, list')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-i', action='store_true', help='install one or more tools from positional tool names')
    group.add_argument('-u', action='store_true', help='uninstall one or more tools from positional tool names')
    group.add_argument('-l', action='store_true', help='list available tools')
    parser.add_argument('-p', '--project-root', help='target project root (required for install/uninstall)')
    args = parser.parse_args()

    registry, tools = load_tools()
    action, raw_tool_names = resolve_action(args.args, args.i, args.u, args.l)
    if action == 'list':
        for item in registry['tools']:
            print(f"{item['name']}\t{', '.join(item['kind'])}")
        return 0

    if not args.project_root:
        fail('project root is required for install/uninstall')
    tool_names = normalize_tool_names(raw_tool_names)
    if not tool_names:
        fail('at least one tool name is required for install/uninstall')

    project_root = Path(args.project_root).resolve()
    if project_root.exists() and not project_root.is_dir():
        fail(f'project root must be a directory: {project_root}')

    grouped: list[tuple[str, tuple[ToolEntry, ...]]] = []
    selected_env_keys: list[tuple[str, EnvKey]] = []
    seen_targets: set[Path] = set()
    for tool_name in tool_names:
        tool = tools.get(tool_name)
        if tool is None:
            fail(f'Unknown tool: {tool_name}')
        entries = build_tool_entries(project_root, tool_name, tool, seen_targets)
        grouped.append((tool_name, entries))
        selected_env_keys.extend((tool_name, env_key) for env_key in tool['env_keys'])

    env_plan = (
        prepare_uninstall_env(project_root, selected_env_keys)
        if action == 'uninstall'
        else prepare_install_env(project_root, selected_env_keys)
    )

    grouped, receipts = prepare_owned_changes(project_root, action, grouped)
    paths = transaction_paths(grouped, env_plan) + tuple(receipts)

    def apply() -> None:
        apply_tool_changes(project_root, action, grouped, env_plan)
        apply_receipts(receipts, project_root)

    run_transaction(
        project_root,
        paths,
        apply,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
