#!/usr/bin/env python3
"""Run a small speculative-decoding benchmark matrix against llama-server."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_MODES = {
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


def request_json(url: str, payload: dict[str, Any] | None = None, timeout: float = 5.0) -> Any:
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


def wait_for_server(base_url: str, proc: subprocess.Popen[str], timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited early with code {proc.returncode}")
        try:
            request_json(f"{base_url}/health", timeout=1.0)
            return
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(0.25)
    raise TimeoutError(f"server did not become healthy within {timeout_s}s: {last_error}")


def load_trace(path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))

    proposed = sum(int(row.get("proposed_tokens") or 0) for row in rows)
    accepted = sum(int(row.get("accepted_tokens") or 0) for row in rows)
    verify_us = sum(int(row.get("verification_us") or 0) for row in rows)

    by_proposer: dict[str, dict[str, int | float]] = {}
    for row in rows:
        name = str(row.get("proposer") or "unknown")
        item = by_proposer.setdefault(
            name,
            {"rounds": 0, "proposed_tokens": 0, "accepted_tokens": 0, "verification_us": 0},
        )
        item["rounds"] = int(item["rounds"]) + 1
        item["proposed_tokens"] = int(item["proposed_tokens"]) + int(row.get("proposed_tokens") or 0)
        item["accepted_tokens"] = int(item["accepted_tokens"]) + int(row.get("accepted_tokens") or 0)
        item["verification_us"] = int(item["verification_us"]) + int(row.get("verification_us") or 0)

    for item in by_proposer.values():
        p = int(item["proposed_tokens"])
        item["acceptance_rate"] = (int(item["accepted_tokens"]) / p) if p else 0.0

    return {
        "rounds": len(rows),
        "proposed_tokens": proposed,
        "accepted_tokens": accepted,
        "acceptance_rate": accepted / proposed if proposed else 0.0,
        "verification_ms": verify_us / 1000.0,
        "by_proposer": by_proposer,
    }


def extract_server_metrics(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        return {}

    out: dict[str, Any] = {}
    for key in (
        "tokens_predicted",
        "tokens_evaluated",
        "generation_settings",
        "timings",
        "stop",
        "stopped_eos",
        "stopped_limit",
    ):
        if key in response:
            out[key] = response[key]
    return out


def run_mode(
    name: str,
    mode_args: list[str],
    base_cmd: list[str],
    prompt: str,
    n_predict: int,
    port: int,
    startup_timeout: float,
    output_dir: Path,
) -> dict[str, Any]:
    mode_dir = output_dir / name
    mode_dir.mkdir(parents=True, exist_ok=True)
    trace_path = mode_dir / "speculative.ndjson"
    log_path = mode_dir / "server.log"

    if trace_path.exists():
        trace_path.unlink()

    cmd = [*base_cmd, "--port", str(port), *mode_args]
    env = os.environ.copy()
    env["IK_LLAMA_SPEC_TRACE"] = str(trace_path.resolve())

    started = time.monotonic()
    response: Any = {}
    request_wall_s = 0.0

    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        try:
            base_url = f"http://127.0.0.1:{port}"
            wait_for_server(base_url, proc, startup_timeout)
            request_started = time.monotonic()
            response = request_json(
                f"{base_url}/completion",
                {
                    "prompt": prompt,
                    "n_predict": n_predict,
                    "temperature": 0,
                    "stream": False,
                },
                timeout=max(60.0, startup_timeout),
            )
            request_wall_s = time.monotonic() - request_started
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    (mode_dir / "response.json").write_text(
        json.dumps(response, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    content = response.get("content") if isinstance(response, dict) else None
    if isinstance(content, str):
        (mode_dir / "output.txt").write_text(content, encoding="utf-8")

    return {
        "mode": name,
        "command": cmd,
        "startup_plus_request_s": time.monotonic() - started,
        "request_wall_s": request_wall_s,
        "server": extract_server_metrics(response),
        "speculation": load_trace(trace_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-cmd", required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("semantic-decoding-results"))
    parser.add_argument("--n-predict", type=int, default=512)
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--startup-timeout", type=float, default=120.0)
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=sorted(DEFAULT_MODES),
        default=list(DEFAULT_MODES),
    )
    args = parser.parse_args()

    base_cmd = shlex.split(args.base_cmd, posix=os.name != "nt")
    if not base_cmd:
        parser.error("--base-cmd produced an empty command")

    prompt = args.prompt_file.read_text(encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for index, name in enumerate(args.modes):
        result = run_mode(
            name=name,
            mode_args=DEFAULT_MODES[name],
            base_cmd=base_cmd,
            prompt=prompt,
            n_predict=args.n_predict,
            port=args.port + index,
            startup_timeout=args.startup_timeout,
            output_dir=args.output_dir,
        )
        results.append(result)
        print(json.dumps(result, ensure_ascii=False))

    summary = {
        "schema_version": 1,
        "prompt_file": str(args.prompt_file),
        "results": results,
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
