# Developing Semantic Decoding Experiments

## Branch policy

Research work currently lives on:

`research/semantic-decoding`

Keep `main` close to upstream `ik_llama.cpp` until an experiment has demonstrated value and its integration path is clear.

## Before changing the decode path

1. State the hypothesis in `HYPOTHESES.md`.
2. Define the metric that can falsify it.
3. Prefer existing counters/hooks over new instrumentation.
4. Keep new behavior opt-in.
5. Preserve baseline sampling semantics unless the experiment explicitly studies quality-changing behavior.

## Adding a proposer

A new proposer should ideally:

1. plug into the existing speculative stage abstraction;
2. return target-vocabulary token candidates;
3. reuse the existing target verification path;
4. expose normal speculative counters;
5. add proposer-specific metadata only when necessary.

Do not add a parallel target verifier unless the existing abstraction cannot represent the experiment.

## Coding rules for instrumentation

- No token text/code content in traces by default.
- Keep trace records small.
- Avoid allocations or I/O when tracing is disabled.
- Do not use traced runs for headline performance numbers.
- Treat schema changes as versioned compatibility changes.

## Tooling checks

Self-tests:

```text
python experiments/semantic-decoding/tools/test_trace_tools.py
```

Preflight:

```text
python experiments/semantic-decoding/tools/run_matrix.py ... --dry-run
```

Build and runtime validation still require a real local `llama-server` build and model.

## Review checklist

Before accepting a decoding experiment:

- Does baseline behavior remain unchanged when disabled?
- Is output equivalent to deterministic baseline where losslessness is claimed?
- Are startup and request latency measured separately?
- Is trace I/O excluded from performance measurements?
- Are proposal coverage and acceptance both reported?
- Are failures/fallbacks visible rather than silently omitted?
- Is the comparison repeated and order-balanced?
- Does the experiment improve solved-task cost, not only tokens/s?
