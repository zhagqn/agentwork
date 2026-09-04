# Install Browser Tool

## What gets installed
- `.shared/skills/browser/SKILL.md`
- `.shared/skills/browser/scripts/browser-run.sh`
- thin wrappers for Codex / Claude / Cursor / Pi

## Install
```bash
python3 install-tool.py install browser -p <path>
python3 install-tool.py -i browser -p <path>
```

## Uninstall
```bash
python3 install-tool.py uninstall browser -p <path>
python3 install-tool.py -u browser -p <path>
```

## After install
- separately install `agent-browser >= 0.26.0`; the latest stable release is
  recommended
- verify the selected executable with `agent-browser --version`
- follow the upstream installation steps if a browser runtime is also needed
- browser outputs default to project `.tmp/browser`
- choose a task-scoped `AGENT_BROWSER_SESSION` and reuse it for each wrapper call in that task
- CDP auto-discovery is disabled by default; set `BROWSER_CDP_PREFER=1` only when the selected target is intentional

The agentwork tool pack does not install or distribute the external CLI, its
source, its documentation, or a copy of its license. `agent-browser` remains
subject to its own
[Apache-2.0 license](https://github.com/vercel-labs/agent-browser/blob/main/LICENSE);
see the [official repository](https://github.com/vercel-labs/agent-browser) for
current installation instructions.

Releases older than 0.26.0 do not provide the complete
`agent-browser skills get core` contract. The shared skill can fall back to
`--help` for limited compatibility, but upgrading is required when the older
command surface cannot satisfy the task.
