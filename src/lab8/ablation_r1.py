"""R1 ablation: compare the normal orchestrator with one order-only investigator.

The production orchestrator's other two read calls (policy summary and refund
history) are recorded for trace/context but do not affect its decision. This
variant changes only the allowed investigator read set, retaining lookup_order
and the same quoting, model, host, evaluator, and data path.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from unittest.mock import patch

from lab8.db import connect
from lab8.handoff import make_handoff as _make_handoff
from lab8.schemas import make_run_id as _make_run_id
from lab8.shapes import orchestrator


def _order_only_handoff(**kwargs):
    kwargs["allowed_tools"] = ["lookup_order"]
    return _make_handoff(**kwargs)


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
):
    """Run the existing orchestrator with one read-only investigator call."""
    conn: sqlite3.Connection = connect(store_path)
    try:
        with (
            patch.object(orchestrator, "make_handoff", _order_only_handoff),
            patch.object(
                orchestrator,
                "make_run_id",
                lambda _shape, cid, trial_seed: _make_run_id(
                    "r1_order_only", cid, trial_seed
                ),
            ),
        ):
            result = orchestrator._run(
                conn, claim_id, seed=seed, crash_at=crash_at
            )
            return replace(result, shape="r1_order_only")
    finally:
        conn.close()
