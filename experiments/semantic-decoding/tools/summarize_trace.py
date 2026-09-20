#!/usr/bin/env python3
"""Summarize IK_LLAMA_SPEC_TRACE NDJSON using only the Python stdlib."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


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


def read_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            # A process killed during append can leave only the final line truncated.
            if index == len(lines) - 1:
                continue
            raise
        if isinstance(row, dict):
            rows.append(row)
    return rows


def summarize_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    spec = [row for row in rows if row.get("type") == "speculation"]
    verified = [
        row for row in spec
        if row.get("outcome") in {"partial_accept", "full_accept"}
    ]
    proposals = [row for row in spec if int(row.get("proposed_tokens") or 0) > 0]

    proposed = [int(row.get("proposed_tokens") or 0) for row in proposals]
    accepted = [int(row.get("accepted_tokens") or 0) for row in verified]
    verification_ms = [
        float(row.get("verification_total_us") or 0) / 1000.0 for row in verified
    ]

    total_proposed = sum(proposed)
    total_accepted = sum(int(row.get("accepted_tokens") or 0) for row in verified)
    outcomes = Counter(str(row.get("outcome") or "unknown") for row in spec)

    by_proposer: dict[str, dict[str, Any]] = {}
    for row in spec:
        name = str(row.get("proposer") or "unknown")
        item = by_proposer.setdefault(
            name,
            {
                "attempts": 0,
                "proposals": 0,
                "verified_rounds": 0,
                "proposed_tokens": 0,
                "accepted_tokens": 0,
                "outcomes": {},
            },
        )
        item["attempts"] += 1
        n_proposed = int(row.get("proposed_tokens") or 0)
        n_accepted = int(row.get("accepted_tokens") or 0)
        if n_proposed > 0:
            item["proposals"] += 1
            item["proposed_tokens"] += n_proposed
        if row.get("outcome") in {"partial_accept", "full_accept"}:
            item["verified_rounds"] += 1
            item["accepted_tokens"] += n_accepted
        outcome = str(row.get("outcome") or "unknown")
        item["outcomes"][outcome] = int(item["outcomes"].get(outcome, 0)) + 1

    for item in by_proposer.values():
        attempts = int(item["attempts"])
        proposed_tokens = int(item["proposed_tokens"])
        item["proposal_coverage"] = (
            int(item["proposals"]) / attempts if attempts else 0.0
        )
        item["acceptance_rate"] = (
            int(item["accepted_tokens"]) / proposed_tokens if proposed_tokens else 0.0
        )

    return {
        "schema_version": 1,
        "records": len(spec),
        "verified_rounds": len(verified),
        "proposal_rounds": len(proposals),
        "proposal_coverage": len(proposals) / len(spec) if spec else 0.0,
        "proposed_tokens": total_proposed,
        "accepted_tokens": total_accepted,
        "acceptance_rate": total_accepted / total_proposed if total_proposed else 0.0,
        "accepted_per_verified_round_mean": (
            statistics.fmean(accepted) if accepted else 0.0
        ),
        "accepted_per_verified_round_p50": percentile(
            [float(v) for v in accepted], 0.50
        ),
        "accepted_per_verified_round_p95": percentile(
            [float(v) for v in accepted], 0.95
        ),
        "verification_total_ms_p50": percentile(verification_ms, 0.50),
        "verification_total_ms_p95": percentile(verification_ms, 0.95),
        "outcomes": dict(sorted(outcomes.items())),
        "by_proposer": by_proposer,
    }


def summarize_file(path: Path) -> dict[str, Any]:
    return summarize_rows(read_ndjson(path))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    output = summarize_file(args.trace)
    print(json.dumps(output, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
