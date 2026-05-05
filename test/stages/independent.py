from __future__ import annotations

from test import harness


name = 'independent_commands'


def run(ctx) -> dict:
    return harness.run_workflow_commands_stage(
        ctx.provider,
        ctx.model,
        ctx.reasoning_effort,
        ctx.service_tier,
        ctx.project,
        ctx.results,
    )
