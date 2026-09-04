#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / 'install-tool.py'
TOOLS_ROOT = REPO_ROOT / '.agentwork/tools'
REGISTRY = TOOLS_ROOT / 'registry.json'
BROWSER_ROOT = TOOLS_ROOT / 'browser'
PROHIBITED_BROWSER_TEXT = tuple(
    ''.join(parts)
    for parts in (
        ('同步', '来源'),
        ('保持上游', '核心流程'),
        ('Ref Lifecycle ', '(Important)'),
        ('Semantic ', 'Locators'),
        ('Deep-Dive ', 'Documentation'),
        ('Ready-to-Use ', 'Templates'),
    )
)


def tree_snapshot(path: Path) -> dict[str, tuple[str, bytes | str | None]]:
    paths = [path]
    if path.is_dir() and not path.is_symlink():
        paths.extend(sorted(path.rglob('*')))
    snapshot: dict[str, tuple[str, bytes | str | None]] = {}
    for item in paths:
        relative = '.' if item == path else item.relative_to(path).as_posix()
        if item.is_symlink():
            snapshot[relative] = ('symlink', os.readlink(item))
        elif item.is_dir():
            snapshot[relative] = ('directory', None)
        else:
            snapshot[relative] = ('file', item.read_bytes())
    return snapshot


def browser_source_violations(root: Path) -> set[str]:
    sources = '\n'.join(
        path.read_text() for path in root.rglob('*') if path.is_file()
    )
    return {text for text in PROHIBITED_BROWSER_TEXT if text in sources}


class ToolCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='agentwork-tool-catalog-')
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        boundary = self.project / 'staged-boundary.txt'
        boundary.write_text('keep staged\n')
        subprocess.run(['git', '-C', str(self.project), 'add', boundary.name], check=True)
        registry = json.loads(REGISTRY.read_text())
        self.tools = registry['tools']
        self.names = [tool['name'] for tool in self.tools]

    def run_tools(self, command: str, *names: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ['python3', str(INSTALLER), command, *names, '-p', str(self.project)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def run_installer(self, command: str) -> subprocess.CompletedProcess[str]:
        return self.run_tools(command, *self.names)

    def staged_hash(self) -> str:
        diff = subprocess.run(
            ['git', '-C', str(self.project), 'diff', '--cached', '--binary'],
            check=True,
            capture_output=True,
        ).stdout
        return hashlib.sha256(diff).hexdigest()

    def project_snapshot(self) -> dict[str, tuple[str, bytes | str | None]]:
        return {
            key: value
            for key, value in tree_snapshot(self.project).items()
            if key != '.git' and not key.startswith('.git/')
        }

    def manifest_entries(self):
        for tool in self.tools:
            tool_root = TOOLS_ROOT / tool['dir']
            manifest = json.loads((tool_root / 'tool.json').read_text())
            self.assertEqual(manifest['name'], tool['name'])
            self.assertEqual(manifest['kind'], tool['kind'])
            for entry in manifest['entries']:
                yield tool_root / entry['from'], self.project / entry['to']

    def assert_manifest_exact(self) -> None:
        for source, target in self.manifest_entries():
            with self.subTest(target=target.relative_to(self.project)):
                self.assertTrue(target.exists() or target.is_symlink())
                self.assertEqual(tree_snapshot(target), tree_snapshot(source))

    def test_full_catalog_install_reinstall_and_uninstall_round_trip(self) -> None:
        staged_before = self.staged_hash()
        self.run_installer('install')
        self.assert_manifest_exact()
        first_install = self.project_snapshot()
        self.run_installer('install')
        self.assert_manifest_exact()
        self.assertEqual(self.project_snapshot(), first_install)
        self.assertEqual(self.staged_hash(), staged_before)

        self.run_installer('uninstall')
        for _, target in self.manifest_entries():
            self.assertFalse(target.exists() or target.is_symlink())
        after_uninstall = self.project_snapshot()
        self.run_installer('uninstall')
        self.assertEqual(self.project_snapshot(), after_uninstall)
        self.assertEqual(self.staged_hash(), staged_before)
        self.assertEqual((self.project / '.env').read_bytes(), b'')
        self.assertEqual((self.project / '.gitignore').read_text(), '.env\n')

    def test_browser_pack_uses_external_dynamic_contract(self) -> None:
        manifest = json.loads((BROWSER_ROOT / 'tool.json').read_text())
        targets = {entry['to'] for entry in manifest['entries']}
        self.assertEqual(
            targets,
            {
                '.shared/skills/browser/SKILL.md',
                '.shared/skills/browser/scripts/browser-run.sh',
                '.codex/skills/browser/SKILL.md',
                '.claude/skills/browser/SKILL.md',
                '.pi/skills/browser',
                '.cursor/rules/browser.mdc',
            },
        )
        self.assertNotIn('THIRD_PARTY_NOTICES', json.dumps(manifest))

        shared_skill = (
            BROWSER_ROOT / 'shared/skills/browser/SKILL.md'
        ).read_text()
        self.assertIn('agent-browser` 0.26.0 or newer', shared_skill)
        self.assertIn('skills get core', shared_skill)
        self.assertIn('--help', shared_skill)
        self.assertIn('does not install the CLI', shared_skill)

        self.assertEqual(browser_source_violations(BROWSER_ROOT), set())

        wrappers = (
            BROWSER_ROOT / 'codex/skills/browser/SKILL.md',
            BROWSER_ROOT / 'claude/skills/browser/SKILL.md',
            BROWSER_ROOT / 'pi/skills/browser/SKILL.md',
            BROWSER_ROOT / 'cursor/rules/browser.mdc',
        )
        for wrapper in wrappers:
            content = wrapper.read_text()
            with self.subTest(wrapper=wrapper.relative_to(BROWSER_ROOT)):
                self.assertIn('.shared/skills/browser/SKILL.md', content)
                self.assertIn(
                    '.shared/skills/browser/scripts/browser-run.sh', content
                )
                self.assertNotIn('skills get core', content)

    def test_browser_source_check_rejects_historical_structure(self) -> None:
        fixture = Path(self.temp.name) / 'browser-source-fixture'
        shutil.copytree(BROWSER_ROOT, fixture)
        skill = fixture / 'shared/skills/browser/SKILL.md'
        skill.write_text(
            skill.read_text() + f'\n## {PROHIBITED_BROWSER_TEXT[-1]}\n'
        )
        self.assertEqual(
            browser_source_violations(fixture),
            {PROHIBITED_BROWSER_TEXT[-1]},
        )


class BrowserWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(
            prefix='agentwork-browser-wrapper-',
            dir='/tmp',
        )
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'deep/project/path'
        self.project.mkdir(parents=True)
        result = subprocess.run(
            ['python3', str(INSTALLER), 'install', 'browser', '-p', str(self.project)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.wrapper = (
            self.project / '.shared/skills/browser/scripts/browser-run.sh'
        )
        self.nested_workdir = self.project / 'nested/deeper'
        self.nested_workdir.mkdir(parents=True)
        self.runtime_root = Path(f'/tmp/agentwork-browser-{os.getuid()}')
        self.fake_bin = self.root / 'bin'
        self.fake_bin.mkdir()
        fake_browser = self.fake_bin / 'agent-browser'
        fake_browser.write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            '{\n'
            "  printf 'ARGS'\n"
            "  printf '\\t%s' \"$@\"\n"
            "  printf '\\nPROFILE=%s\\n' \"${AGENT_BROWSER_PROFILE-}\"\n"
            "  printf 'SOCKET_DIR=%s\\n' \"${AGENT_BROWSER_SOCKET_DIR-}\"\n"
            "  printf 'PROJECT_KEY=%s\\n' \"${AGENTWORK_BROWSER_PROJECT_KEY-}\"\n"
            "  printf 'PWD=%s\\n' \"${PWD-}\"\n"
            '} >> "${BROWSER_CAPTURE_FILE}"\n'
        )
        fake_browser.chmod(0o755)
        self.capture = self.root / 'capture.txt'
        self.capture.write_text('')
        self.addCleanup(self.cleanup_runtime_dirs)
        self.env = os.environ.copy()
        self.env.update(
            {
                'PATH': f'{self.fake_bin}{os.pathsep}{self.env["PATH"]}',
                'BROWSER_CAPTURE_FILE': str(self.capture),
                'AGENT_BROWSER_SESSION': 'route12',
            }
        )

    def run_wrapper(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(self.wrapper), *args],
            cwd=cwd or self.project,
            env=env or self.env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result

    def cleanup_runtime_dirs(self) -> None:
        socket_dirs = {
            Path(line.removeprefix('SOCKET_DIR='))
            for line in self.capture.read_text().splitlines()
            if line.startswith('SOCKET_DIR=')
        }
        owned_runtime_dirs = {
            path
            for path in socket_dirs
            if path.parent == self.runtime_root
            and len(path.name) == 16
            and all(char in '0123456789abcdef' for char in path.name)
        }
        for path in (*owned_runtime_dirs, self.runtime_root):
            try:
                path.rmdir()
            except (FileNotFoundError, OSError):
                pass

    def test_routes_runtime_cdp_and_default_artifacts(self) -> None:
        stale_runtime = self.project / '.tmp/browser/agent-browser'
        stale_runtime.mkdir(parents=True)
        stale_socket = stale_runtime / 'route12.sock'
        with socket.socket(socket.AF_UNIX) as unix_socket:
            unix_socket.bind(str(stale_socket))

        paths = dict(
            line.split('=', 1)
            for line in self.run_wrapper('paths').stdout.splitlines()
            if '=' in line
        )
        socket_dir = Path(paths['SOCKET_DIR'])
        self.assertEqual(paths['BROWSER_CDP_PREFER'], '0')
        self.assertEqual(paths['AGENT_BROWSER_SESSION'], 'route12')
        self.assertFalse(socket_dir.is_relative_to(self.project))
        self.assertTrue(
            socket_dir.is_relative_to(Path(f'/tmp/agentwork-browser-{os.getuid()}'))
        )
        recommended_session = 'task-0123456789ab'
        self.assertGreater(
            len(os.fsencode(stale_runtime / f'{recommended_session}.sock')),
            103,
        )
        self.assertLessEqual(
            len(os.fsencode(socket_dir / f'{recommended_session}.sock')),
            103,
        )

        self.run_wrapper('skills', 'get', 'core')
        self.run_wrapper('--help')

        fallback_env = self.env | {
            'BROWSER_CDP_PREFER': '1',
            'BROWSER_CDP_TARGET': '65530',
        }
        self.run_wrapper('open', 'http://127.0.0.1/test', env=fallback_env)
        self.assertFalse(stale_socket.exists())

        endpoint = 'ws://127.0.0.1:19444/devtools/browser/test'

        class CdpHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                body = json.dumps({'webSocketDebuggerUrl': endpoint}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(('127.0.0.1', 0), CdpHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        cdp_env = self.env | {
            'BROWSER_CDP_PREFER': '1',
            'BROWSER_CDP_TARGET': str(server.server_port),
        }
        self.run_wrapper('open', 'http://127.0.0.1/test', env=cdp_env)
        self.run_wrapper(
            '--cdp',
            'ws://explicit.test/devtools/browser/1',
            'open',
            'http://127.0.0.1/test',
            env=cdp_env,
        )
        self.run_wrapper('screenshot', env=fallback_env)

        capture = self.capture.read_text()
        self.assertIn('ARGS\tskills\tget\tcore\nPROFILE=', capture)
        self.assertNotIn('ARGS\t--cdp\t', capture.split('ARGS\topen', 1)[0])
        self.assertIn('ARGS\topen\thttp://127.0.0.1/test\nPROFILE=', capture)
        self.assertIn(
            f'ARGS\t--cdp\t{endpoint}\topen\thttp://127.0.0.1/test',
            capture,
        )
        self.assertIn(
            'ARGS\t--cdp\tws://explicit.test/devtools/browser/1\topen',
            capture,
        )
        self.assertRegex(
            capture,
            r'ARGS\tscreenshot\t.+/\.tmp/browser/screenshot-\d{8}-\d{6}\.png',
        )

    def test_stateful_commands_require_a_safe_explicit_session(self) -> None:
        no_session = self.env.copy()
        no_session.pop('AGENT_BROWSER_SESSION')
        result = subprocess.run(
            [str(self.wrapper), 'open', 'http://127.0.0.1/test'],
            cwd=self.project,
            env=no_session,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('任务级 AGENT_BROWSER_SESSION', result.stderr)

        invalid_session = self.env | {'AGENT_BROWSER_SESSION': '../escape'}
        result = subprocess.run(
            [str(self.wrapper), 'open', 'http://127.0.0.1/test'],
            cwd=self.project,
            env=invalid_session,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('AGENT_BROWSER_SESSION 必须', result.stderr)

        reserved_session = self.env | {'AGENT_BROWSER_SESSION': 'default'}
        result = subprocess.run(
            [str(self.wrapper), 'open', 'http://127.0.0.1/test'],
            cwd=self.project,
            env=reserved_session,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn('不能使用保留名', result.stderr)

        self.run_wrapper('--help', env=no_session)

    def test_cleanup_is_scoped_to_the_current_session(self) -> None:
        paths = dict(
            line.split('=', 1)
            for line in self.run_wrapper('paths').stdout.splitlines()
            if '=' in line
        )
        socket_dir = paths['SOCKET_DIR']

        def start_daemon(session: str) -> subprocess.Popen[str]:
            daemon_env = os.environ.copy()
            daemon_env.update(
                {
                    'AGENT_BROWSER_DAEMON': '1',
                    'AGENT_BROWSER_SESSION': session,
                    'AGENT_BROWSER_SOCKET_DIR': socket_dir,
                    'PWD': str(self.project),
                }
            )
            process = subprocess.Popen(
                [sys.executable, '-c', 'import time; time.sleep(30)'],
                cwd=self.project,
                env=daemon_env,
                text=True,
            )

            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                details = subprocess.run(
                    ['ps', 'eww', '-p', str(process.pid), '-o', 'command='],
                    text=True,
                    capture_output=True,
                    check=False,
                ).stdout
                if (
                    'AGENT_BROWSER_DAEMON=1' in details
                    and f'AGENT_BROWSER_SESSION={session}' in details
                ):
                    break
                time.sleep(0.02)
            else:
                process.kill()
                process.wait(timeout=3)
                self.fail(f'daemon fixture did not become observable: {session}')

            def stop_daemon() -> None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=3)

            self.addCleanup(stop_daemon)
            return process

        current = start_daemon('current12')
        other = start_daemon('other12')
        wrapper_env = self.env | {
            'AGENT_BROWSER_SESSION': 'current12',
            'AGENT_BROWSER_SOCKET_DIR': socket_dir,
            'BROWSER_CDP_PREFER': '0',
        }
        self.run_wrapper('open', 'http://127.0.0.1/test', env=wrapper_env)
        current.wait(timeout=3)
        self.assertIsNotNone(current.returncode)
        self.assertIsNone(other.poll())

    def test_nested_invocations_use_a_stable_project_identity(self) -> None:
        nested_env = self.env | {'BROWSER_CDP_PREFER': '0'}
        self.run_wrapper(
            'open',
            'http://127.0.0.1/test',
            env=nested_env,
            cwd=self.nested_workdir,
        )
        self.run_wrapper(
            'get',
            'url',
            env=nested_env,
            cwd=self.nested_workdir,
        )

        capture = self.capture.read_text()
        project_key = hashlib.sha256(
            str(self.project).encode()
        ).hexdigest()[:16]
        self.assertIn('ARGS\topen\thttp://127.0.0.1/test', capture)
        self.assertIn('ARGS\tget\turl', capture)
        self.assertEqual(capture.count(f'PROJECT_KEY={project_key}\n'), 2)
        working_dirs = [
            Path(line.removeprefix('PWD='))
            for line in capture.splitlines()
            if line.startswith('PWD=')
        ]
        self.assertEqual(len(working_dirs), 2)
        self.assertTrue(
            all(path.samefile(self.nested_workdir) for path in working_dirs)
        )
        self.assertFalse(self.nested_workdir.joinpath('.tmp').exists())

    def test_missing_cli_returns_127(self) -> None:
        result = subprocess.run(
            [str(self.wrapper), '--version'],
            cwd=self.project,
            env={'PATH': '/usr/bin:/bin'},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 127)
        self.assertIn('未找到 agent-browser', result.stderr)

if __name__ == '__main__':
    unittest.main(verbosity=2)
