#!/usr/bin/env python3
"""Summarize Semantic Decoding JSON traces using only the Python stdlib."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def summarize(trace: dict[str, Any]) -> dict[str, Any]:
    spec = [e for e in trace.get("events", []) if e.get("type") == "speculation"]

    proposed = [int(e.get("proposed_tokens") or 0) for e in spec]
    accepted = [int(e.get("accepted_tokens") or 0) for e in spec]
    verify_ms = [
        float(e["duration_ms"])
        for e in spec
        if e.get("duration_ms") is not None
    ]

    total_proposed = sum(proposed)
    total_accepted = sum(accepted)

    by_proposer: dict[str, dict[str, int]] = {}
    for e in spec:
        name = str(e.get("proposer") or "unknown")
        row = by_proposer.setdefault(
            name, {"cycles": 0, "proposed_tokens": 0, "accepted_tokens": 0}
        )
        row["cycles"] += 1
        row["proposed_tokens"] += int(e.get("proposed_tokens") or 0)
        row["accepted_tokens"] += int(e.get("accepted_tokens") or 0)

    for row in by_proposer.values():
        p = row["proposed_tokens"]
        row["acceptance_rate"] = (row["accepted_tokens"] / p) if p else 0.0

    summary = trace.get("summary", {})
    return {
        "schema_version": trace.get("schema_version"),
        "task_id": trace.get("run", {}).get("task_id"),
        "mode": trace.get("run", {}).get("mode"),
        "result": summary.get("result"),
        "wall_time_ms": summary.get("wall_time_ms"),
        "generated_tokens": summary.get("generated_tokens"),
        "target_eval_count": summary.get("target_eval_count"),
        "speculation_cycles": len(spec),
        "proposed_tokens": total_proposed,
        "accepted_tokens": total_accepted,
        "acceptance_rate": (
            total_accepted / total_proposed if total_proposed else 0.0
        ),
        "accepted_per_cycle_mean": (
            statistics.fmean(accepted) if accepted else 0.0
        ),
        "accepted_per_cycle_p50": percentile([float(v) for v in accepted], 0.50),
        "accepted_per_cycle_p95": percentile([float(v) for v in accepted], 0.95),
        "verification_ms_p50": percentile(verify_ms, 0.50),
        "verification_ms_p95": percentile(verify_ms, 0.95),
        "by_proposer": by_proposer,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.trace.read_text(encoding="utf-8"))
    output = summarize(data)
    print(json.dumps(output, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
