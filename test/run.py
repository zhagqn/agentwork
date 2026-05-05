from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test import harness
from test.stages import independent, install, session


STAGES = [install, independent, session]
STAGE_BY_NAME = {stage.name: stage for stage in STAGES}
STAGE_ALIASES = {
    'install': install.name,
    'independent': independent.name,
    'session': session.name,
}


@dataclass
class RunContext:
    run_id: str
    run_root: Path
    results: Path
    project: Path
    provider: str
    model: str | None
    reasoning_effort: str | None
    service_tier: str | None
    started_at: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run or resume the integrated agentwork test.')
    parser.add_argument('--provider', choices=harness.SUPPORTED_PROVIDERS, help='provider used for workflow command execution')
    parser.add_argument('--model', help='provider model for workflow command execution, for example gpt-5.4')
    parser.add_argument('--reasoning-effort', help='provider reasoning effort, for example xhigh for codex')
    parser.add_argument('--service-tier', help='Codex service tier, for example fast')
    parser.add_argument('--fast', action='store_true', help='shortcut for --service-tier fast when provider is codex')
    parser.add_argument('--run-id', help='optional run id; default uses timestamp')
    parser.add_argument('--resume', help='resume a run directory or run id under .tmp/integrated-harness/runs')
    parser.add_argument(
        '--stage',
        choices=['all', 'install', 'independent', 'session', *STAGE_BY_NAME.keys()],
        default='all',
        help='run all remaining stages or a single stage',
    )
    return parser.parse_args()


def resolve_run_root(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    return harness.RUNS_ROOT / value


def normalize_stage(value: str) -> str:
    return STAGE_ALIASES.get(value, value)


def load_latest(run_root: Path) -> dict:
    latest = run_root / 'results' / 'latest.json'
    if not latest.exists():
        raise SystemExit(f'cannot resume without results/latest.json: {latest}')
    return json.loads(latest.read_text(encoding='utf-8'))


def create_context(args: argparse.Namespace) -> tuple[RunContext, list[dict]]:
    service_tier = args.service_tier
    if args.fast:
        if service_tier and service_tier != 'fast':
            raise SystemExit('--fast conflicts with --service-tier values other than fast')
        service_tier = 'fast'

    if args.resume:
        run_root = resolve_run_root(args.resume)
        summary = load_latest(run_root)
        provider = args.provider or summary.get('provider')
        if not provider:
            raise SystemExit('resume summary is missing provider')
        ctx = RunContext(
            run_id=summary['run_id'],
            run_root=run_root,
            results=run_root / 'results',
            project=run_root / 'project',
            provider=provider,
            model=args.model if args.model is not None else summary.get('model'),
            reasoning_effort=(
                args.reasoning_effort if args.reasoning_effort is not None else summary.get('reasoning_effort')
            ),
            service_tier=service_tier if service_tier is not None else summary.get('service_tier'),
            started_at=summary.get('started_at') or harness.now_iso(),
        )
        return ctx, list(summary.get('stages', []))

    provider = harness.which_provider(args.provider)
    if service_tier and provider != 'codex':
        raise SystemExit('--service-tier/--fast is only supported for --provider codex')
    run_id = args.run_id or harness.now_id()
    run_root = harness.RUNS_ROOT / run_id
    if run_root.exists():
        raise SystemExit(f'run directory already exists: {run_root}')
    results = run_root / 'results'
    results.mkdir(parents=True, exist_ok=True)
    ctx = RunContext(
        run_id=run_id,
        run_root=run_root,
        results=results,
        project=run_root / 'project',
        provider=provider,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        service_tier=service_tier,
        started_at=harness.now_iso(),
    )
    harness.write_reports(ctx.results, 'latest', build_summary(ctx, [], 'running'))
    return ctx, []


def build_summary(ctx: RunContext, stages: list[dict], status: str) -> dict:
    return harness.build_summary(
        ctx.run_id,
        ctx.provider,
        ctx.model,
        ctx.reasoning_effort,
        ctx.service_tier,
        ctx.started_at,
        ctx.run_root,
        ctx.project,
        stages,
        status,
    )


def stage_names_to_run(requested: str, stages: list[dict]) -> list[str]:
    if requested != 'all':
        return [normalize_stage(requested)]
    completed = {stage['name'] for stage in stages if stage.get('ok')}
    return [stage.name for stage in STAGES if stage.name not in completed]


def replace_stage(stages: list[dict], stage: dict) -> list[dict]:
    order = [item.name for item in STAGES]
    stage_index = order.index(stage['name'])
    return [item for item in stages if order.index(item['name']) < stage_index] + [stage]


def main() -> int:
    args = parse_args()
    ctx, stages = create_context(args)
    if ctx.service_tier and ctx.provider != 'codex':
        raise SystemExit('--service-tier/--fast is only supported for --provider codex')

    harness.log(
        f'[run] id={ctx.run_id} provider={ctx.provider} model={ctx.model or ""} '
        f'reasoning_effort={ctx.reasoning_effort or ""} service_tier={ctx.service_tier or ""}'
    )
    harness.log(f'[run] root={ctx.run_root}')
    harness.log(f'[run] project={ctx.project}')

    for stage_name in stage_names_to_run(args.stage, stages):
        stage = STAGE_BY_NAME[stage_name].run(ctx)
        stages = replace_stage(stages, stage)
        current_status = 'fail' if not stage['ok'] else 'running'
        harness.write_reports(ctx.results, 'latest', build_summary(ctx, stages, current_status))
        if not stage['ok']:
            break

    ok = bool(stages) and all(stage['ok'] for stage in stages)
    summary = build_summary(ctx, stages, 'pass' if ok else 'fail')
    summary['finished_at'] = harness.now_iso()
    harness.write_reports(ctx.results, 'latest', summary)
    harness.write_reports(ctx.results, 'summary', summary)
    harness.log(f'[summary] {summary["status"].upper()} -> {ctx.results / "summary.md"}')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
