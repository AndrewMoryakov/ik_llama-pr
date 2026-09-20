# Semantic Decoding Lab

Experimental workbench for reducing expensive sequential target-model computation in CPU-first agentic inference.

## Goal

Optimize **time and target compute per solved task**, not only raw tokens/second.

The lab studies complementary mechanisms:

1. lossless speculative execution (suffix, n-gram, MTP, future proposers);
2. repository/reference reuse (COPY/span proposals);
3. compact reasoning and agent protocols;
4. compact edit/action IR;
5. semantic routing between cheap proposers and normal target decoding;
6. later: activation steering / adaptive-compute experiments.

## Design rules

- Keep upstream `ik_llama.cpp` behavior unchanged unless an experiment is explicitly enabled.
- Instrument before optimizing.
- Compare against a reproducible baseline.
- Preserve enough trace data to replay and audit a run.
- Measure solved-task outcomes in addition to token throughput.
- Prefer lossless mechanisms first; isolate quality-changing experiments.

## Initial milestones

### M0 — foundation
- hypotheses and metrics;
- versioned JSON trace schema;
- trace summarizer.

### M1 — speculative observability
Capture per speculative cycle:
- proposer;
- proposed token count;
- accepted token count;
- rejection position;
- verification time;
- target evaluation count.

### M2 — real agent traces
Run identical coding tasks under:
- baseline;
- n-gram;
- suffix;
- n-gram -> MTP where supported.

### M3 — repo-copy proposer
Prototype a proposer that retrieves candidate continuations from repository spans and verifies them with the normal target model.

### M4 — semantic routing
Route between suffix, n-gram, repo-copy, and normal decoding using cheap observable signals.

## Layout

```text
experiments/semantic-decoding/
  README.md
  HYPOTHESES.md
  METRICS.md
  trace.schema.json
  tools/
    summarize_trace.py
```

This directory intentionally starts outside the core decode path. Engine changes should be small, measurable, and introduced only when required by an experiment.


## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — system boundaries, invariants, and extension points.
- [TRACE_FORMAT.md](TRACE_FORMAT.md) — canonical NDJSON runtime trace contract.
- [METRICS.md](METRICS.md) — measurement definitions and benchmark methodology.
- [RUN.md](RUN.md) — build, preflight, benchmark, and trace workflow.
- [DEVELOPING.md](DEVELOPING.md) — rules for adding instrumentation and proposers.
- [HYPOTHESES.md](HYPOTHESES.md) — falsifiable research hypotheses.
- [CODE_MAP.md](CODE_MAP.md) — existing ik_llama speculative hooks reused by the project.
- [ROADMAP.md](ROADMAP.md) — milestones from observability through model-level experiments.
- [RESULTS_TEMPLATE.md](RESULTS_TEMPLATE.md) — reproducible record for real CPU benchmark results.

## Current status

M1 implementation is complete in the research branch, but local Windows/MSVC build and real-model runtime validation are still required before benchmark results should be trusted.
