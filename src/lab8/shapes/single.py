"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("single", claim_id, seed))

    def decide(observation: dict[str, Any]) -> dict[str, Any]:
        last_tool = observation.get("last_tool")
        result = observation.get("last_result") or {}
        complete(
            budget,
            seed=seed,
            purpose="react",
            prompt=f"single-agent step={last_tool or 'start'}; choose a read-only tool",
        )

        if last_tool is None:
            return {"tool": "get_claim_view", "args": {"claim_id": claim_id}}
        if last_tool == "get_claim_view":
            if not result.get("found"):
                return {"final": {"status": "failed", "proposal_amount": 0, "reason": "unknown_claim"}}
            if not result.get("order_id"):
                return {
                    "final": {
                        "status": "needs_info",
                        "proposal_amount": 0,
                        "reason": "missing_order_id",
                    }
                }
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": result["order_id"],
                    "principal_id": result["principal_id"],
                },
            }
        if last_tool == "lookup_order":
            if not result.get("visible"):
                return {
                    "final": {
                        "status": "escalated",
                        "proposal_amount": 0,
                        "reason": result.get("reason"),
                    }
                }
            return {"tool": "compute_compensation", "args": {"order": result["order"]}}
        if last_tool == "compute_compensation":
            amount = int(result.get("amount_vnd", 0))
            return {
                "final": {
                    "status": "resolved" if amount > 0 else "denied",
                    "proposal_amount": amount,
                    "reason": result.get("reason"),
                    "quote": result,
                }
            }
        return {"final": {"status": "failed", "proposal_amount": 0, "reason": "unexpected_react_state"}}

    outcome = run_react(
        conn,
        budget,
        observation={"claim": {"claim_id": claim_id}},
        decide=decide,
        max_steps=8,
        worker=True,
    )
    final = outcome["final"]
    status = final["status"]
    proposal = int(final.get("proposal_amount", 0))

    trace.add("react", {"stopped": outcome["stopped"], "status": status})
    last_tool = outcome["observation"].get("last_tool")
    last_result = outcome["observation"].get("last_result") or {}
    if last_tool == "get_claim_view":
        trace.add(
            "claim_view",
            {
                key: last_result[key]
                for key in ("found", "claim_id", "order_id")
                if key in last_result
            },
        )
    elif last_tool == "lookup_order":
        trace.add(
            "order_lookup",
            {
                key: last_result[key]
                for key in ("visible", "reason", "order_id")
                if key in last_result
            },
        )
    elif last_tool == "compute_compensation":
        trace.add("quote", safe_dump(last_result))

    if status in ("needs_info", "escalated", "failed"):
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=final.get("reason"),
        )

    if proposal <= 0:
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=final.get("reason"),
        )

    try:
        refund = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not refund["ok"]:
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed" if refund["conflict"] else "denied",
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=refund["reason"],
        )
    return finish(
        conn,
        shape="single",
        claim_id=claim_id,
        seed=seed,
        status="resolved",
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=None,
    )
