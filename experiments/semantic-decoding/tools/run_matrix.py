#!/usr/bin/env python3
"""Benchmark speculative modes without contaminating timing with trace I/O."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from summarize_trace import summarize_file


DEFAULT_MODES: dict[str, list[str]] = {
    "baseline": [],
    "ngram-mod": [
        "--spec-type",
        "ngram-mod:n_max=64,n_min=2,ngram_size_n=8",
    ],
    "suffix": [
        "--spec-type",
        "suffix:n_max=16,n_min=2,suffix_min_match_len=5,suffix_max_depth=64",
    ],
}


def request_json(url: str, payload: dict[str, Any] | None, timeout: float) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def wait_for_server(base_url: str, proc: subprocess.Popen[str], timeout_s: float) -> float:
    started = time.monotonic()
    deadline = started + timeout_s
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited early with code {proc.returncode}")
        try:
            request_json(f"{base_url}/health", None, 1.0)
            return time.monotonic() - started
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(0.25)

    raise TimeoutError(
        f"server did not become healthy within {timeout_s}s: {last_error}"
    )


def output_text(response: Any) -> str:
    if not isinstance(response, dict):
        return ""
    content = response.get("content")
    return content if isinstance(content, str) else ""


def output_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_server_metrics(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {}

    keys = (
        "tokens_predicted",
        "tokens_evaluated",
        "generation_settings",
        "timings",
        "stop",
        "stopped_eos",
        "stopped_limit",
    )
    return {key: response[key] for key in keys if key in response}


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_base_command(args: argparse.Namespace) -> list[str]:
    command = [str(args.server), "-m", str(args.model)]
    if args.threads is not None:
        command.extend(["-t", str(args.threads)])
    if args.ctx_size is not None:
        command.extend(["-c", str(args.ctx_size)])
    for item in args.server_arg:
        command.append(item)
    return command


def completion_payload(prompt: str, n_predict: int) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "n_predict": n_predict,
        "temperature": 0,
        "stream": False,
    }


def run_once(
    *,
    label: str,
    mode: str,
    mode_args: list[str],
    base_command: list[str],
    prompt: str,
    n_predict: int,
    port: int,
    startup_timeout: float,
    request_timeout: float,
    output_dir: Path,
    trace: bool,
) -> dict[str, Any]:
    run_dir = output_dir / label / mode
    run_dir.mkdir(parents=True, exist_ok=True)

    trace_path = run_dir / "speculative.ndjson"
    log_path = run_dir / "server.log"
    response_path = run_dir / "response.json"
    output_path = run_dir / "output.txt"

    if trace_path.exists():
        trace_path.unlink()

    command = [*base_command, "--port", str(port), *mode_args]
    env = os.environ.copy()
    if trace:
        env["IK_LLAMA_SPEC_TRACE"] = str(trace_path.resolve())
    else:
        env.pop("IK_LLAMA_SPEC_TRACE", None)

    response: Any = {}
    startup_s = 0.0
    request_s = 0.0

    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        try:
            base_url = f"http://127.0.0.1:{port}"
            startup_s = wait_for_server(base_url, proc, startup_timeout)

            started = time.monotonic()
            response = request_json(
                f"{base_url}/completion",
                completion_payload(prompt, n_predict),
                request_timeout,
            )
            request_s = time.monotonic() - started
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    response_path.write_text(
        json.dumps(response, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    text = output_text(response)
    output_path.write_text(text, encoding="utf-8")

    result: dict[str, Any] = {
        "mode": mode,
        "trace_enabled": trace,
        "command": command,
        "startup_s": startup_s,
        "request_s": request_s,
        "output_sha256": output_hash(text),
        "output_chars": len(text),
        "server": extract_server_metrics(response),
    }

    if trace:
        result["trace"] = summarize_file(trace_path) if trace_path.exists() else {}

    return result


def rotated_orders(modes: list[str], repeats: int) -> list[list[str]]:
    if not modes:
        return []
    return [
        modes[(index % len(modes)) :] + modes[: (index % len(modes))]
        for index in range(repeats)
    ]


def aggregate_performance(
    results: list[dict[str, Any]],
    modes: list[str],
) -> dict[str, Any]:
    baseline_hashes = [
        row["output_sha256"] for row in results if row["mode"] == "baseline"
    ]
    canonical_hash = baseline_hashes[0] if baseline_hashes else None

    aggregate: dict[str, Any] = {}
    for mode in modes:
        rows = [row for row in results if row["mode"] == mode]
        request_values = [float(row["request_s"]) for row in rows]
        startup_values = [float(row["startup_s"]) for row in rows]
        hashes = [row["output_sha256"] for row in rows]

        aggregate[mode] = {
            "runs": len(rows),
            "request_s_median": statistics.median(request_values)
            if request_values
            else None,
            "request_s_min": min(request_values) if request_values else None,
            "request_s_max": max(request_values) if request_values else None,
            "startup_s_median": statistics.median(startup_values)
            if startup_values
            else None,
            "output_hashes": sorted(set(hashes)),
            "output_equal_to_baseline": (
                canonical_hash is not None and all(h == canonical_hash for h in hashes)
            ),
        }

    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--threads", type=int)
    parser.add_argument("--ctx-size", type=int)
    parser.add_argument(
        "--server-arg",
        action="append",
        default=[],
        help="Append one raw llama-server argv item. Repeat as needed.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("semantic-decoding-results"),
    )
    parser.add_argument("--n-predict", type=int, default=512)
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--startup-timeout", type=float, default=180.0)
    parser.add_argument("--request-timeout", type=float, default=600.0)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--trace-pass", action="store_true")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=sorted(DEFAULT_MODES),
        default=list(DEFAULT_MODES),
    )
    args = parser.parse_args()

    if args.repeats < 1:
        parser.error("--repeats must be >= 1")
    if args.warmups < 0:
        parser.error("--warmups must be >= 0")

    prompt = args.prompt_file.read_text(encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    base_command = build_base_command(args)
    modes = list(args.modes)

    warmup_results: list[dict[str, Any]] = []
    for warmup_index in range(args.warmups):
        for mode_index, mode in enumerate(modes):
            warmup_results.append(
                run_once(
                    label=f"warmup-{warmup_index + 1:02d}",
                    mode=mode,
                    mode_args=DEFAULT_MODES[mode],
                    base_command=base_command,
                    prompt=prompt,
                    n_predict=args.n_predict,
                    port=args.port + mode_index,
                    startup_timeout=args.startup_timeout,
                    request_timeout=args.request_timeout,
                    output_dir=args.output_dir,
                    trace=False,
                )
            )

    performance_results: list[dict[str, Any]] = []
    for repeat_index, order in enumerate(rotated_orders(modes, args.repeats)):
        for order_index, mode in enumerate(order):
            result = run_once(
                label=f"performance-{repeat_index + 1:02d}",
                mode=mode,
                mode_args=DEFAULT_MODES[mode],
                base_command=base_command,
                prompt=prompt,
                n_predict=args.n_predict,
                port=args.port + order_index,
                startup_timeout=args.startup_timeout,
                request_timeout=args.request_timeout,
                output_dir=args.output_dir,
                trace=False,
            )
            performance_results.append(result)
            print(json.dumps(result, ensure_ascii=False))

    trace_results: list[dict[str, Any]] = []
    if args.trace_pass:
        for mode_index, mode in enumerate(modes):
            result = run_once(
                label="trace",
                mode=mode,
                mode_args=DEFAULT_MODES[mode],
                base_command=base_command,
                prompt=prompt,
                n_predict=args.n_predict,
                port=args.port + mode_index,
                startup_timeout=args.startup_timeout,
                request_timeout=args.request_timeout,
                output_dir=args.output_dir,
                trace=True,
            )
            trace_results.append(result)

    summary = {
        "schema_version": 2,
        "git_commit": git_commit(),
        "server": str(args.server),
        "model": str(args.model),
        "prompt_file": str(args.prompt_file),
        "threads": args.threads,
        "ctx_size": args.ctx_size,
        "n_predict": args.n_predict,
        "repeats": args.repeats,
        "warmups": args.warmups,
        "modes": modes,
        "performance": {
            "runs": performance_results,
            "aggregate": aggregate_performance(performance_results, modes),
        },
        "trace": trace_results,
    }

    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
