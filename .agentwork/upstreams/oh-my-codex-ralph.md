# Ralph upstream mapping — oh-my-codex

This document tracks how `Yeachan-Heo/oh-my-codex` Ralph should be consumed as an upstream foundation for `agentwork`.

## Upstream source
- repo: `https://github.com/Yeachan-Heo/oh-my-codex`
- local mirror: `.tmp/oh-my-codex/`
- current inspected commit: `d5975af01a4bb8a7d3c68d4131b31029566380ac`
- release note at inspection time: `0.12.5`

## Update
```bash
if [ ! -d .tmp/oh-my-codex/.git ]; then
  git clone --depth=1 https://github.com/Yeachan-Heo/oh-my-codex.git .tmp/oh-my-codex
else
  git -C .tmp/oh-my-codex fetch --depth=1 origin main
  git -C .tmp/oh-my-codex reset --hard origin/main
fi
git -C .tmp/oh-my-codex log -1 --oneline
```

## Why this lives in `.agentwork`
Ralph upstream sync, comparison, and extraction are source-maintenance concerns.
They do not belong in `.shared`, which is for project-consumable workflow contracts.

## What agentwork should import
### Reusable core
1. context snapshot requirement
2. frozen lifecycle phases
3. verify/fix loop semantics
4. completion requires fresh evidence
5. cancellation as terminalization
6. canonical Ralph artifact layout

### Reusable command/runtime ideas
1. persistent execution policy over an existing execution surface
2. context/progress bootstrap before loop begins
3. append-only upgrade strategy for legacy artifacts
4. explicit status/phase visibility
5. subagent-first delegation for bounded independent work

## What agentwork should not import directly
1. tmux/team/ultrawork coupling
2. HUD/runtime display wiring
3. state-server-specific contracts
4. upstream-specific scope precedence rules
5. plugin/catalog/runtime glue

## Recommended agentwork target shape
### `.shared`
- no separate `/ralph` command in first pass
- import Ralph as execution policy on `/exec` and `/session exec`
- keep reusable Ralph semantics in command docs/templates rather than a parallel workflow tree

### `.tmp`
- `.tmp/agentwork/ralph/{slug}/context.md`
- `.tmp/agentwork/ralph/{slug}/prd.md`
- `.tmp/agentwork/ralph/{slug}/progress.json`
- `.tmp/agentwork/ralph/{slug}/review.md`

### `.agentwork`
- this mapping file

## Update workflow
1. 按上面的命令刷新 `.tmp/oh-my-codex`
2. Inspect upstream diffs relevant to Ralph
3. Compare them against this file and the current agentwork Ralph plan
4. Selectively port only reusable core semantics into `.shared`
5. Keep upstream-specific runtime pieces out unless agentwork truly needs them
