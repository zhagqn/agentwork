# agentwork

agentwork is a repository-native workflow layer for coding agents. It turns
ambiguous work into an explicit `brain`, `plan`, `exec`, and `review` delivery
flow, with repository-backed Case snapshots that can move across Codex, Claude
Code, OpenCode, Cursor, and Pi.

Coding agents are good at producing changes, but sustained work also needs
clear decision gates, recoverable task state, review boundaries, and a way to
carry the same intent between tools. agentwork keeps those concerns in the
repository instead of relying on one provider's private conversation state.

## What agentwork provides

- **An explicit delivery flow.** [`brain`](.shared/commands/brain.md) clarifies
  the problem, [`plan`](.shared/commands/plan.md) creates a verifiable work
  breakdown, [`exec`](.shared/commands/exec.md) advances a bounded batch, and
  [`review`](.shared/commands/review.md) checks both the work and its workflow
  artifacts.
- **Recoverable, opt-in task state.** Cases are repository files with
  explicit load and update rules; old task context is never loaded merely
  because it exists. See the
  [Case workflow](.shared/patterns/case-workflow.md).
- **One shared contract, thin platform adapters.** The durable workflow lives
  in [`.shared/`](.shared/INDEX.md). Codex, Claude Code, OpenCode, Cursor, and
  Pi receive small native entry points instead of separate copies of the core
  rules. See the
  [platform adapter model](.shared/patterns/platform-adapter.md).
- **A conservative Codex integration.** The bootstrap installs project-level
  skills and keeps `AGENTS.md` as the stable entry point. Custom agents and
  Codex configuration remain project-owned.
- **Optional capability packs.** Browser automation, Figma, Android, Godot,
  architecture documentation, and other integrations stay outside the core
  workflow and are installed only when a project needs them. The registry
  in [`.agentwork/tools/`](.agentwork/tools/README.md) is the source of truth.
- **Default capabilities.** anydoc and research are distributed as default
  skills for Codex, Claude Code, Cursor, Pi, and the shared layer. Distribution
  does not install runtime dependencies: anydoc's npm package is installed in a
  project only when an agent needs to parse an office document, and research
  ships the routing contract alone. research is the single research entry point
  and picks the narrowest provider itself; remote providers such as Exa and
  Octocode remain separate optional packs that never install MCP servers, CLIs,
  or binaries, never create or modify `.env`, never touch platform MCP private
  configuration, and never send private material or credentials to a remote
  service. Default distribution is not a stability claim: research's routing
  contract stays non-stable until the gates in
  [`.agentwork/evals/research/`](.agentwork/evals/research/README.md) pass.
- **Local, deterministic checks.** Workflow artifacts and bootstrap behavior
  have repository-owned checks, while live provider tests remain explicit
  compatibility investigations rather than hidden prerequisites.

## Upgrading Projects With Optional Research

Older projects may have `.agentwork/tool-receipts/research.json`. Bootstrap
refuses overlapping tool claims before writing, including missing files and
projects already carrying both receipts. Keep the previous source checkout
that still lists research, and use its `install-tool.py uninstall research -p
PROJECT` before running the new `install-bootstrap.py -p PROJECT`. The current
tool installer no longer recognizes research. Do not delete the receipt alone.

If the old uninstall reports modified files, first back up those files outside
the managed paths and review the differences. Restore the matching installed
version only after preserving your edits, uninstall with the old source, then
bootstrap and reapply the required edits. Without the old source or a verified
backup, stop and reconcile ownership manually. Migration never silently removes
user modifications. After migration, repeating the old uninstall has no receipt
to act on and leaves the bootstrap files intact.

`verify.sh` is a source-repository gate and is not distributed to projects.
Previously distributed copies are retired only when their old receipt digest
matches; customized or unowned copies are preserved. Target projects can run
`.shared/scripts/agentwork-check.py self-test` and explicit artifact checks.

## What agentwork is not

agentwork is not an AI model, an agent runtime, or a replacement for the native
capabilities of Codex and other coding tools. It does not silently install MCP
servers, copy every optional tool into every project, or treat generated plans
as permission to edit code. anydoc supplies a default document parsing rule,
but its runtime package is still installed only at project scope and on demand.
Platform-native capabilities remain preferred;
the shared layer exists to make intent, handoff, and verification portable.

This repository is the source and maintenance repository for agentwork. The
files installed into another project are a deliberately smaller subset of the
repository's bootstrap and optional tool sources.

## Requirements

- Python 3.11 or newer
- Git
- At least one supported coding agent: Codex, Claude Code, OpenCode, Cursor, or
  Pi

The core bootstrap has no package installation step. anydoc's runtime package
is installed only when needed; other optional tool packs may have their own
runtime, authentication, or MCP requirements.

## Quick start

Clone this source repository, then install the core workflow into an existing
or new project directory:

```bash
git clone https://github.com/zhagqn/agentwork.git
cd agentwork
python3 install-bootstrap.py -p /absolute/path/to/project
```

The bootstrap installs the shared workflow contract and thin native entry
points for all supported agents. It does not install custom agents. Existing project
files and unrelated Codex configuration are preserved; conflicting managed
paths fail explicitly instead of being silently overwritten.

Upgrading removes the retired `luna_worker` registration only when its managed
block matches the known generated version. Its agent file is removed only when
ownership is verified and no remaining role references it. Modified files and
configuration blocks are preserved and reported for manual review.

Open the target project in your coding agent and move a task through the
workflow:

```text
brain   Clarify the goal, constraints, alternatives, and success criteria.
plan    Turn the confirmed design into bounded, verifiable tasks.
case    Create, load, or sync an explicit repository-backed task snapshot.
exec    Execute a small batch from the plan after explicit authorization.
review  Check both the resulting work and the workflow artifacts.
commit  Commit only the reviewed Git boundary selected by the user.
```

Use the platform's native syntax. Codex discovers these as project skills such
as `$brain`, `$plan`, `$exec`, and `$review`; Claude Code and OpenCode expose
slash commands. Pi exposes `/brain`, `/plan`, `/exec`, `/review`, `/commit`,
and `/case` as project prompt templates. Cursor uses its project rule and
can follow the same shared command files directly.

Start Pi from the target repository root and approve project trust before using
the `.pi/prompts/` entry points. Non-interactive Pi modes do not display a trust
prompt; use `--approve` only after deciding the project is trusted. That flag is
a one-run project-resource trust override, not a sandbox or tool-command
approval. Pi's built-in `/session` describes its native conversation session;
use `/case` for agentwork's explicit repository-backed handoff and recovery
workflow. Other platforms use the same shared Case entry.

The core bootstrap deliberately does **not** install optional tool runtimes,
configure MCP servers or providers, or import existing task state. It does
install the anydoc capability rules; an agent installs the pinned npm package
in the project only when a document task requires it.

### Updating an existing project

Before installing or refreshing agentwork in an existing project, start from a
state you can review and restore: commit or otherwise back up current work,
then inspect the resulting diff after the command finishes.

The bootstrap records its directly copied files in
`.agentwork/bootstrap-install-state.json`. On later runs, it refreshes a file
only when ownership can be established from the current source, an agentwork
generated marker, or the previous receipt. Project and Case indexes,
`.gitignore`, and Codex configuration use bounded managed blocks so content
outside those blocks remains project-owned. Partial, reversed, duplicated, or
conflicting managed state stops the install before target writes begin.

The installer keeps `.tmp/` protection as the final ignore rule, moving its
managed block when necessary. This takes precedence over earlier exceptions
without deleting project-owned rules. To retain a specific temporary artifact,
explicitly force-add that file. Ignore rules do not untrack existing files.

If a target write fails or the process is interrupted, the installer restores
the target paths managed by that run. This is a filesystem rollback for one
installer process, not concurrency isolation: it cannot undo unrelated changes
made by another process while the install is running. Review the diff before
continuing, and keep project-specific additions outside directly managed files
and managed blocks.

## Optional tools

List the current tool catalog from the agentwork source checkout:

```bash
python3 install-tool.py list
```

Install only what a target project needs. For example, to add browser
automation:

```bash
python3 install-tool.py install browser -p /absolute/path/to/project
```

research is not in this catalog. It is a default capability that arrives with
the core bootstrap, so `install-tool.py install research` fails with
`Unknown tool: research`.

Each tool pack declares its installed files in `tool.json` and documents its
external prerequisites in `INSTALL.md`. The catalog registry, rather than this
README, remains the authoritative tool list. Tool installation and removal run
preflight checks and restore affected project files after ordinary write
failures or interruption.

Tool files are tracked individually in `.agentwork/tool-receipts/*.json`.
Receipts also record empty directories created by the installer.
Existing files without a matching receipt, or with local edits, stop the
operation before writes; older installations without receipts are not
automatically adopted. Reinstalling preserves additional project files inside
tool directories. Uninstall removes only unchanged receipted files and empty
directories. Keep receipts with the project when moving its installed tools.

The optional [browser tool pack](.agentwork/tools/browser/README.md) integrates
with a separately installed `agent-browser >= 0.26.0`; it does not bundle that
CLI, its source, its documentation, or its license. The external CLI remains
subject to its own Apache-2.0 license. Browser commands require an explicit
task-scoped `AGENT_BROWSER_SESSION`; automatic CDP discovery is disabled unless
the project deliberately sets `BROWSER_CDP_PREFER=1`.

## Repository model

| Path | Responsibility |
| --- | --- |
| [`.shared/`](.shared/INDEX.md) | Provider-neutral workflow contracts, constraints, patterns, templates, and deterministic checks. |
| [`.agentwork/bootstrap/`](.agentwork/bootstrap/README.md) | Sources and renderer for the minimal files installed into target projects. |
| [`.agentwork/tools/`](.agentwork/tools/README.md) | Optional capability-pack sources, manifests, and installation guidance. |
| [`.codex/`](.codex) | Self-hosted Codex skills for this source repository. |
| [`.claude/`](.claude), [`.opencode/`](.opencode), [`.cursor/`](.cursor) | Self-hosted thin platform adapters generated from the bootstrap source. |
| `.pi/prompts/` | Self-hosted Pi project prompt templates generated from the bootstrap source. |
| `.pi/skills/` | Pi skill entry points; anydoc is part of the core bootstrap, while other tool packs remain explicit. |
| [`docs/architecture/`](docs/architecture/README.md) | Example and generated output for the optional `arch` tool, not the architecture of an agentwork business service. |

The source repository self-hosts the same bootstrap layout it distributes.
Generated platform adapters are maintained from
`.agentwork/bootstrap/spec.json` and its renderer; durable workflow behavior
belongs in `.shared/`.

## Platform support

| Platform | Installed entry points | Boundary |
| --- | --- | --- |
| Codex | `AGENTS.md`, project skills | Uses native Codex capabilities first; agentwork supplies shared artifacts without installing custom agents. |
| Claude Code | `CLAUDE.md`, project commands, optional skills | Thin commands delegate to the shared workflow; runtime loops and permissions remain platform concerns. |
| OpenCode | `AGENTS.md`, generated project commands | Commands inject shared definitions; provider, model, plugin, MCP, and permission configuration remain project-owned. |
| Cursor | Project rule plus `AGENTS.md` fallback | Uses native editing and diagnostics while shared command files provide the portable workflow contract. |
| Pi | `AGENTS.md`, six project prompts under `.pi/prompts/`, default anydoc skill | Static adapter contract is based on Pi `v0.84.4`; start from the repository root and trust the project. The core bootstrap does not install Pi, extensions, subagents, or optional tool runtimes; Browser, Research, and CodeGraph can add explicit project skills through their own tool packs. |

Platform discovery, permissions, sandbox behavior, and runtime orchestration can
change independently. The
[platform adapter model](.shared/patterns/platform-adapter.md) records the
supported boundaries and fallback behavior; it does not claim identical
runtime behavior across tools.

## Verification

Run deterministic workflow checks from the source checkout:

```bash
python3 .shared/scripts/agentwork-check.py self-test
```

Run the source repository's installer and routing tests:

```bash
python3 -m unittest discover -s .agentwork/tests -p 'test_*.py'
```

Live provider and MCP checks are intentionally separate compatibility
investigations. They are not hidden requirements for the core workflow.

## Project status and limits

- agentwork is currently installed from a source checkout; it is not published
  as a Python package.
- Core workflow behavior is provider-neutral, but native command discovery and
  runtime behavior still depend on each supported agent.
- Pi compatibility currently records the `v0.84.4` prompt and trust structure;
  live runtime discovery is tracked as a separate compatibility smoke rather
  than implied by deterministic bootstrap tests.
- Optional tool packs may reference external projects or require separately
  installed CLIs, credentials, or MCP configuration.
- Bootstrap updates preserve project-owned files where ownership is ambiguous
  and stop on conflicts that cannot be resolved conservatively.
- Plans and Cases are coordination artifacts, not automatic permission to
  modify code, external systems, Git history, or staged changes.

## Contributing

Issues and focused pull requests are welcome. Before changing generated
platform adapters, identify their source in `.agentwork/bootstrap/` or the
relevant optional tool pack. Keep shared behavior in `.shared/`, preserve the
documented platform boundaries, and run the verification commands above.

## License

Original agentwork content is available under the [MIT License](LICENSE),
Copyright (c) 2026 zhagqn.

The root license applies to this source repository. The bootstrap and optional
tool installers do not add or replace a target project's license file.

Optional external tools and dependencies retain their own licenses and are not
relicensed by agentwork's root MIT License.
