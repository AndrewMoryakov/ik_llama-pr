#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from run_matrix import aggregate_performance, planned_commands, render_report, rotated_orders
from summarize_trace import read_ndjson, summarize_rows


class TraceToolsTests(unittest.TestCase):
    def test_truncated_final_line_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.ndjson"
            path.write_text(
                json.dumps({
                    "schema_version": 1,
                    "type": "speculation",
                    "outcome": "full_accept",
                    "proposer": "suffix",
                    "proposed_tokens": 4,
                    "accepted_tokens": 4,
                    "verification_total_us": 1000,
                })
                + "\n"
                + '{"schema_version":1,"type":"spec',
                encoding="utf-8",
            )
            rows = read_ndjson(path)
            self.assertEqual(len(rows), 1)

    def test_summary_counts_coverage_and_acceptance(self) -> None:
        rows = [
            {
                "type": "speculation",
                "outcome": "no_proposal",
                "proposer": "suffix",
                "proposed_tokens": 0,
                "accepted_tokens": 0,
                "verification_total_us": 0,
            },
            {
                "type": "speculation",
                "outcome": "partial_accept",
                "proposer": "suffix",
                "proposed_tokens": 4,
                "accepted_tokens": 2,
                "verification_total_us": 2000,
            },
            {
                "type": "speculation",
                "outcome": "full_accept",
                "proposer": "suffix",
                "proposed_tokens": 3,
                "accepted_tokens": 3,
                "verification_total_us": 1000,
            },
        ]
        summary = summarize_rows(rows)
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["proposal_rounds"], 2)
        self.assertAlmostEqual(summary["proposal_coverage"], 2 / 3)
        self.assertEqual(summary["proposed_tokens"], 7)
        self.assertEqual(summary["accepted_tokens"], 5)
        self.assertAlmostEqual(summary["acceptance_rate"], 5 / 7)

    def test_rotated_orders(self) -> None:
        self.assertEqual(
            rotated_orders(["baseline", "suffix", "ngram-mod"], 3),
            [
                ["baseline", "suffix", "ngram-mod"],
                ["suffix", "ngram-mod", "baseline"],
                ["ngram-mod", "baseline", "suffix"],
            ],
        )


    def test_planned_commands_preserve_space_bearing_paths(self) -> None:
        base = [
            r"O:\\user files\\build\\llama-server.exe",
            "-m",
            r"O:\\user files\\Models\\qwen.gguf",
        ]
        plan = planned_commands(base, ["baseline", "suffix"], 18080)
        self.assertEqual(plan["baseline"][0], base[0])
        self.assertEqual(plan["baseline"][2], base[2])
        self.assertEqual(plan["suffix"][0], base[0])
        self.assertIn("suffix:n_max=16,n_min=2", plan["suffix"][-1])

    def test_report_contains_speedup_and_equivalence(self) -> None:
        summary = {
            "git_commit": "abc",
            "model": "model.gguf",
            "threads": 16,
            "ctx_size": 8192,
            "repeats": 3,
            "modes": ["baseline", "suffix"],
            "performance": {
                "aggregate": {
                    "baseline": {
                        "request_s_median": 10.0,
                        "request_s_min": 9.5,
                        "request_s_max": 10.5,
                        "output_equal_to_baseline": True,
                    },
                    "suffix": {
                        "request_s_median": 5.0,
                        "request_s_min": 4.8,
                        "request_s_max": 5.2,
                        "output_equal_to_baseline": True,
                    },
                }
            },
            "trace": [],
        }
        report = render_report(summary)
        self.assertIn("2.000x", report)
        self.assertIn("| suffix | 5.000", report)
        self.assertIn("| yes |", report)

    def test_output_equivalence_uses_baseline_hash(self) -> None:
        rows = [
            {
                "mode": "baseline",
                "request_s": 10.0,
                "startup_s": 1.0,
                "output_sha256": "same",
            },
            {
                "mode": "baseline",
                "request_s": 12.0,
                "startup_s": 1.1,
                "output_sha256": "same",
            },
            {
                "mode": "suffix",
                "request_s": 7.0,
                "startup_s": 1.2,
                "output_sha256": "same",
            },
            {
                "mode": "suffix",
                "request_s": 8.0,
                "startup_s": 1.3,
                "output_sha256": "same",
            },
        ]
        aggregate = aggregate_performance(rows, ["baseline", "suffix"])
        self.assertEqual(aggregate["baseline"]["request_s_median"], 11.0)
        self.assertEqual(aggregate["suffix"]["request_s_median"], 7.5)
        self.assertTrue(aggregate["suffix"]["output_equal_to_baseline"])


if __name__ == "__main__":
    unittest.main()
