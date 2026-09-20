# Running the first benchmark

Build llama-server normally, prepare one deterministic prompt, then run the same request in isolated server processes.

## Linux/macOS

    python3 experiments/semantic-decoding/tools/run_matrix.py \
      --base-cmd './build/bin/llama-server -m /models/qwen.gguf -t 16' \
      --prompt-file ./prompt.txt \
      --n-predict 512

## PowerShell

    python experiments/semantic-decoding/tools/run_matrix.py `
      --base-cmd '.\\build\\bin\\Release\\llama-server.exe -m D:\\models\\qwen.gguf -t 16' `
      --prompt-file .\\prompt.txt `
      --n-predict 512

The default matrix is baseline, ngram-mod, and suffix. Each mode starts a fresh server process, so startup-only speculative settings are isolated.

Each mode writes server.log, response.json, output.txt when present, and speculative.ndjson. The root output directory contains summary.json.

## Trace sink

Set IK_LLAMA_SPEC_TRACE to an NDJSON path before starting llama-server to enable per-round tracing. Without this variable, no trace file is written.

Example on PowerShell:

    $env:IK_LLAMA_SPEC_TRACE = "spec.ndjson"
    .\\build\\bin\\Release\\llama-server.exe ...

Each speculative record contains proposer, proposed_tokens, accepted_tokens, rejected_at, verification_us, seq_id, n_past, used_speculative, and failed.

## Interpretation

Compare request wall time, server timing fields, proposed/accepted token counts, acceptance rate, verification time, and output quality. Do not treat a faster failed task as an optimization win; task-level pass/fail evaluation is the next milestone.