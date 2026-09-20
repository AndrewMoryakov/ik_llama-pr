# Running the semantic-decoding benchmark

The benchmark deliberately separates performance measurement from detailed tracing.

## 1. Build

Build `llama-server` normally from the `research/semantic-decoding` branch.

## 2. Preflight

Before loading a model, validate paths and inspect the exact argv that will be passed to each server process:

    python .\experiments\semantic-decoding\tools\run_matrix.py `
      --server ".\build\bin\Release\llama-server.exe" `
      --model "O:\user files\Models\qwen.gguf" `
      --prompt-file ".\prompt.txt" `
      --threads 16 `
      --dry-run

This is especially useful on Windows because paths with spaces remain individual argv entries instead of being re-parsed as a shell command string.

## 3. Performance matrix


PowerShell example:

    python .\experiments\semantic-decoding\tools\run_matrix.py `
      --server ".\build\bin\Release\llama-server.exe" `
      --model "O:\user files\Models\qwen.gguf" `
      --prompt-file ".\prompt.txt" `
      --threads 16 `
      --repeats 3

Linux/macOS example:

    python3 experiments/semantic-decoding/tools/run_matrix.py \
      --server ./build/bin/llama-server \
      --model /models/qwen.gguf \
      --prompt-file ./prompt.txt \
      --threads 16 \
      --repeats 3

Paths are passed directly to `subprocess`; shell quoting is not re-parsed by the runner.

Use repeated `--server-arg` options for additional single argv items, for example:

    --server-arg=-ngl --server-arg=0

The default matrix is:

- baseline;
- ngram-mod;
- suffix.

The runner performs optional warmup processes first, then measured runs with tracing disabled. Mode order is rotated across repeats. `summary.json` reports median/min/max request latency and output hashes, and `REPORT.md` provides a human-readable comparison including speedup versus baseline.

## 4. Optional traced pass

Add:

    --trace-pass

This performs a separate diagnostic run per mode with `IK_LLAMA_SPEC_TRACE` enabled. Trace I/O is therefore excluded from the measured performance runs.

The trace is NDJSON: one independently parseable event per line. A killed process may leave a truncated final line; the summarizer ignores only that final malformed line.

## 5. Standalone trace sink

PowerShell:

    $env:IK_LLAMA_SPEC_TRACE = "spec.ndjson"
    .\build\bin\Release\llama-server.exe ...

Without `IK_LLAMA_SPEC_TRACE`, no trace file is written.

Each event can report:

- outcome;
- proposer;
- proposed_tokens;
- accepted_tokens;
- rejected_at (null when there was no rejection);
- verification_total_us;
- seq_id;
- n_past;
- used_speculative;
- failed.

Summarize a trace with:

    python .\experiments\semantic-decoding\tools\summarize_trace.py spec.ndjson --pretty

## 6. Self-tests

    python .\experiments\semantic-decoding\tools\test_trace_tools.py

These tests require no model.

## Interpretation

For lossless speculative modes, compare:

- median request wall time;
- output_equal_to_baseline;
- proposal coverage;
- acceptance rate;
- accepted tokens per verified round;
- verification total time.

A faster run is not an optimization win if its output/task quality differs unexpectedly. Exact output hashes are a strong sanity check for greedy lossless experiments, but later task-level tests remain the authority for coding-agent quality.
