from __future__ import annotations

from test import harness


name = 'turborepo_iteration_flow'


def run(ctx) -> dict:
    return harness.run_turborepo_flow_stage(
        ctx.provider,
        ctx.model,
        ctx.reasoning_effort,
        ctx.service_tier,
        ctx.project,
        ctx.results,
    )
