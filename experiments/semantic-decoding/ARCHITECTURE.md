# Semantic Decoding Architecture

## Purpose

This research branch explores ways to reduce expensive sequential target-model computation in CPU-first agentic inference.

The project deliberately separates three optimization layers:

1. **Execution** — reduce sequential target verification/decode steps.
2. **Representation** — reduce how many output tokens must be generated.
3. **Protocol** — avoid generating redundant natural-language or source text when a compact action/reference form is sufficient.

Current work is focused on layer 1 while building the measurement foundation required for layers 2 and 3.

## Current data flow

```text
request
  |
  v
llama-server
  |
  v
common_speculative_run_round()
  |
  +--> proposer stage (ngram / suffix / MTP / draft / ...)
  |
  +--> target verification
  |
  +--> accepted prefix / rejection
  |
  +--> optional NDJSON trace
  |
  v
response
```

## Invariants

- Tracing must not affect sampling decisions.
- Performance runs must execute with tracing disabled.
- Detailed trace runs are diagnostic and must not be used as headline latency measurements.
- Lossless speculative methods should reproduce the baseline output under deterministic greedy settings.
- New proposers should reuse the existing speculative verification/commit path instead of creating a second verifier.

## Research extension points

### New proposer

Preferred integration path:

```text
existing speculative abstraction
        |
        +-- ngram
        +-- suffix
        +-- MTP
        +-- repo-copy   <- planned
```

A new proposer should produce ordinary target-vocabulary `llama_tokens` and let the existing target verification path decide the accepted prefix.

### Semantic router

A future router may select among proposers using cheap signals available before a target forward pass.

Examples:

- current syntax/location;
- suffix match length;
- repository-span match score;
- recent proposer success;
- draft length;
- tool/protocol state.

The router should not invoke the target model merely to decide whether to avoid invoking the target model.

## Planned higher-level layers

Later experiments may add:

- compact reasoning protocols;
- compact edit/action IR;
- repository span references;
- activation/control-vector steering;
- adaptive compute;
- training on compressed agent trajectories.

These should remain isolated from lossless decoding experiments so performance and quality effects can be attributed correctly.
