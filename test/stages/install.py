from __future__ import annotations

from test import harness


name = 'install_standard'


def run(ctx) -> dict:
    return harness.run_install_stage(ctx.project, ctx.results)
