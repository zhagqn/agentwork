#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import time
import unittest
import importlib.util

SOURCE_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = SOURCE_ROOT / '.agentwork/tools/octocode/shared/scripts/octocode-mcp.py'
EXPECTED_TOOLS = [
    'ghSearchCode',
    'ghSearchRepos',
    'ghSearchPullRequests',
    'ghSearchIssues',
    'ghSearchCommits',
    'ghGetFileContent',
    'ghViewRepoStructure',
]


def load_wrapper_module():
    spec = importlib.util.spec_from_file_location('octocode_mcp_wrapper', WRAPPER)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load Octocode wrapper')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OctocodeMcpWrapperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_wrapper_pins_read_only_surface_and_preserves_token_environment(self) -> None:
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        capture = self.root / 'capture.json'
        fake_node = bin_dir / 'node'
        fake_node.write_text('#!/bin/sh\nprintf "v20.12.0\\n"\n')
        fake_node.chmod(0o755)
        fake_npx = bin_dir / 'npx'
        fake_npx.write_text(
            '#!/usr/bin/env python3\n'
            'import json, os, pathlib, sys\n'
            "pathlib.Path(os.environ['CAPTURE_PATH']).write_text(json.dumps({\n"
            "    'argv': sys.argv[1:],\n"
            "    'tools': os.environ.get('TOOLS_TO_RUN'),\n"
            "    'local': os.environ.get('ENABLE_LOCAL'),\n"
            "    'clone': os.environ.get('ENABLE_CLONE'),\n"
            "    'releases': os.environ.get('ENABLE_RELEASES'),\n"
            "    'discussions': os.environ.get('ENABLE_DISCUSSIONS'),\n"
            "    'stats': os.environ.get('OCTOCODE_ENABLE_STATS'),\n"
            "    'home': os.environ.get('OCTOCODE_HOME'),\n"
            "    'workspace': os.environ.get('WORKSPACE_ROOT'),\n"
            "    'token_preserved': os.environ.get('GH_TOKEN') == 'not-a-real-token',\n"
            "    'enable_tools_present': 'ENABLE_TOOLS' in os.environ,\n"
            "    'disable_tools_present': 'DISABLE_TOOLS' in os.environ,\n"
            '}))\n'
        )
        fake_npx.chmod(0o755)
        env = os.environ.copy()
        env['PATH'] = f'{bin_dir}{os.pathsep}{env["PATH"]}'
        env['CAPTURE_PATH'] = str(capture)
        env['GH_TOKEN'] = 'not-a-real-token'
        env['TOOLS_TO_RUN'] = 'ghCloneRepo'
        env['ENABLE_TOOLS'] = 'ghCloneRepo'
        env['DISABLE_TOOLS'] = 'ghGetFileContent'

        result = subprocess.run(
            ['python3', str(WRAPPER), '--project-root', str(self.root)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('not-a-real-token', result.stdout + result.stderr)
        recorded = json.loads(capture.read_text())
        self.assertEqual(recorded['argv'], ['-y', 'octocode-mcp@18.2.2'])
        self.assertEqual(recorded['tools'].split(','), EXPECTED_TOOLS)
        self.assertEqual(recorded['local'], 'false')
        self.assertEqual(recorded['clone'], 'false')
        self.assertEqual(recorded['releases'], 'false')
        self.assertEqual(recorded['discussions'], 'false')
        self.assertEqual(recorded['stats'], '0')
        resolved_root = self.root.resolve()
        self.assertEqual(recorded['home'], str(resolved_root / '.tmp/agentwork/octocode'))
        self.assertEqual(recorded['workspace'], str(resolved_root))
        self.assertTrue(recorded['token_preserved'])
        self.assertFalse(recorded['enable_tools_present'])
        self.assertFalse(recorded['disable_tools_present'])

    def test_proxy_rejects_directory_reads_and_filters_schema(self) -> None:
        module = load_wrapper_module()
        blocked = module.blocked_tool_call({
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': 'ghGetFileContent',
                'arguments': {'queries': [{'path': 'src', 'type': 'directory'}]},
            },
        })
        self.assertIn('type=directory is disabled', blocked)
        self.assertIsNone(module.blocked_tool_call({
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'ghGetFileContent',
                'arguments': {'queries': [{'path': 'README.md', 'type': 'file'}]},
            },
        }))
        implicit_file = {
            'jsonrpc': '2.0',
            'id': 4,
            'method': 'tools/call',
            'params': {
                'name': 'ghGetFileContent',
                'arguments': {'queries': [{'path': 'README.md'}]},
            },
        }
        self.assertIsNone(module.blocked_tool_call(implicit_file))
        self.assertEqual(
            implicit_file['params']['arguments']['queries'][0]['type'],
            'file',
        )
        self.assertIn('only allows type=file', module.blocked_tool_call({
            'jsonrpc': '2.0',
            'id': 5,
            'method': 'tools/call',
            'params': {
                'name': 'ghGetFileContent',
                'arguments': {'queries': [{'path': 'README.md', 'type': 'tree'}]},
            },
        }))

        message = {
            'jsonrpc': '2.0',
            'id': 3,
            'result': {
                'tools': [
                    {
                        'name': 'ghGetFileContent',
                        'inputSchema': {
                            'properties': {
                                'queries': {
                                    'items': {
                                        'properties': {
                                            'type': {'enum': ['file', 'directory']},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    {'name': 'ghCloneRepo', 'inputSchema': {}},
                ],
            },
        }
        filtered = module.restrict_tools_list(message)
        self.assertEqual([tool['name'] for tool in filtered['result']['tools']], ['ghGetFileContent'])
        type_schema = filtered['result']['tools'][0]['inputSchema']['properties']['queries']['items']['properties']['type']
        self.assertEqual(type_schema['enum'], ['file'])

    def test_proxy_forwards_coalesced_server_frames_without_waiting_for_eof(self) -> None:
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        fake_node = bin_dir / 'node'
        fake_node.write_text('#!/bin/sh\nprintf "v20.12.0\\n"\n')
        fake_node.chmod(0o755)
        fake_npx = bin_dir / 'npx'
        fake_npx.write_text(
            '#!/usr/bin/env python3\n'
            'import json, sys, time\n'
            'first = json.loads(sys.stdin.readline())\n'
            'second = json.loads(sys.stdin.readline())\n'
            "responses = [\n"
            "    {'jsonrpc': '2.0', 'id': first['id'], 'result': {'protocolVersion': '2025-06-18'}},\n"
            "    {'jsonrpc': '2.0', 'id': second['id'], 'result': {'tools': [\n"
            "        {'name': 'ghGetFileContent', 'inputSchema': {'properties': {'queries': {'items': {'properties': {'type': {'enum': ['file', 'directory']}}}}}}},\n"
            "        {'name': 'ghCloneRepo', 'inputSchema': {}},\n"
            '    ]}},\n'
            ']\n'
            "sys.stdout.write(''.join(json.dumps(item) + '\\n' for item in responses))\n"
            'sys.stdout.flush()\n'
            'sys.stdin.read()\n'
        )
        fake_npx.chmod(0o755)
        env = os.environ.copy()
        env['PATH'] = f'{bin_dir}{os.pathsep}{env["PATH"]}'
        process = subprocess.Popen(
            ['python3', str(WRAPPER), '--project-root', str(self.root)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        self.assertIsNotNone(process.stdin)
        self.assertIsNotNone(process.stdout)
        requests = [
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}},
        ]
        process.stdin.write(b''.join(
            (json.dumps(request) + '\n').encode('utf-8')
            for request in requests
        ))
        process.stdin.flush()
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        output = bytearray()
        # 子进程在 stdin 关闭前不退出；收到响应即可证明代理未等待 EOF。
        # 超时仅限制测试挂起，不把运行时启动速度当成协议契约。
        deadline = time.monotonic() + 10
        try:
            while output.count(b'\n') < 2:
                remaining = deadline - time.monotonic()
                self.assertGreater(remaining, 0, 'proxy waited for child EOF before forwarding buffered frames')
                self.assertTrue(selector.select(remaining), 'proxy response timed out')
                output.extend(os.read(process.stdout.fileno(), 65536))
        finally:
            selector.close()
            process.terminate()
            process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()

        responses = [json.loads(line) for line in output.splitlines()]
        self.assertEqual([response['id'] for response in responses], [1, 2])
        tools = responses[1]['result']['tools']
        self.assertEqual([tool['name'] for tool in tools], ['ghGetFileContent'])
        type_schema = tools[0]['inputSchema']['properties']['queries']['items']['properties']['type']
        self.assertEqual(type_schema['enum'], ['file'])

    def test_proxy_drops_blocked_tool_notifications_before_upstream(self) -> None:
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        capture = self.root / 'requests.json'
        fake_node = bin_dir / 'node'
        fake_node.write_text('#!/bin/sh\nprintf "v20.12.0\\n"\n')
        fake_node.chmod(0o755)
        fake_npx = bin_dir / 'npx'
        fake_npx.write_text(
            '#!/usr/bin/env python3\n'
            'import json, os, pathlib, sys\n'
            "pathlib.Path(os.environ['CAPTURE_PATH']).write_text(json.dumps(list(sys.stdin)))\n"
        )
        fake_npx.chmod(0o755)
        env = os.environ.copy()
        env['PATH'] = f'{bin_dir}{os.pathsep}{env["PATH"]}'
        env['CAPTURE_PATH'] = str(capture)
        notification = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': 'ghGetFileContent',
                'arguments': {
                    'queries': [{'path': 'src', 'type': 'directory'}],
                },
            },
        }
        result = subprocess.run(
            ['python3', str(WRAPPER), '--project-root', str(self.root)],
            input=json.dumps(notification) + '\n',
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(capture.read_text()), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
