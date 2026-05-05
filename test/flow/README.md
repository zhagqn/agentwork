# Integrated Flows

`test/run.py` only orchestrates the harness. Command inputs and provider call order live here so the tested workflow is easier to read and adjust.

- `flow.json`: ordered provider tasks for each integrated stage.
- `independent-*.txt`: standalone command inputs.
- `turborepo-session-*.txt`: session mode command inputs executed as separate calls against the same temporary project.

The files here are not instruction bundles that tell an agent which constraints to read. They simulate user-entered commands such as `$session brain ...`, `$session load ...`, `$session exec`, and `$session review`.

The Turborepo scenario intentionally starts with `$session brain ...`, then runs `$session load {session_file}` before `$session exec` and again before `$session review`. Because every provider task is a separate `codex exec` / `claude -p` process, load and the following command are kept in the same command input to simulate the state that an interactive conversation would otherwise preserve.
