# Roadmap

## M0 — Foundation

Status: complete.

- hypotheses;
- task-level metrics;
- trace schema;
- speculative code map;
- tooling layout.

## M1 — Observability and benchmark validity

Status: implementation complete, local build/runtime validation pending.

- per-round proposer/proposal/acceptance fields;
- NDJSON trace sink;
- proposal coverage outcomes;
- unbiased performance pass;
- optional trace pass;
- repeated measurements;
- rotated mode order;
- deterministic output hash comparison;
- preflight/dry-run;
- generated human-readable report;
- self-tests for trace tooling.

Exit criteria:

- Windows/MSVC build succeeds;
- tooling self-tests pass;
- baseline/ngram/suffix smoke runs complete;
- trace records match aggregate speculative statistics closely enough to trust the instrumentation.

## M2 — Real coding-agent baseline

Status: pending.

Collect representative coding prompts/trajectories and measure:

- baseline latency;
- generated tokens;
- proposal coverage;
- acceptance distribution;
- target evaluations;
- output/task success.

The goal is to identify where target computation is actually spent.

## M3 — Repository-copy proposer

Status: planned.

Hypothesis: a meaningful fraction of coding output can be proposed directly from repository spans.

Initial implementation:

```text
generated prefix
   -> repository span lookup
   -> candidate continuation
   -> existing target verification
```

Required measurements:

- hit/proposal coverage;
- accepted copied tokens;
- acceptance by source type;
- overhead of lookup/indexing;
- end-to-end speedup.

## M4 — Semantic proposer routing

Status: planned.

Choose among:

- suffix;
- n-gram;
- repo-copy;
- MTP/draft where appropriate;
- normal target decode.

Router decisions must be cheap and available before the expensive target forward pass.

## M5 — Compact agent representation

Status: planned.

Explore:

- concise reasoning protocol;
- reference/COPY operations;
- compact edit/action IR;
- task-level output token reduction.

This layer may change model behavior and must be evaluated separately from lossless speculative decoding.

## M6 — Model-level experiments

Status: research.

Possible directions:

- activation/control-vector steering for concise reasoning;
- TokenSkip-like fine-tuning on compressed agent trajectories;
- macro/latent tokens;
- adaptive-depth / early-exit experiments.

These should be attempted only after the task-level benchmark is stable.
