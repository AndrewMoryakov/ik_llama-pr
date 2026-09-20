# Metrics

Raw `tokens/s` is useful, but the primary objective is useful work per expensive target computation.

## Measurement rule

Performance timing and detailed tracing are separate passes.

- Performance pass: `IK_LLAMA_SPEC_TRACE` must be unset.
- Trace pass: records proposal/verification behavior and is not used for headline wall-time comparisons.

This prevents file I/O and trace locking from biasing modes that execute different numbers of speculative rounds.

## Primary task-level metrics

### Wall time per solved task

```text
wall_time_s / solved_task
```

### Generated tokens per solved task

```text
generated_tokens / solved_task
```

### Target evaluations per solved task

Counts expensive sequential target verification/decode evaluations.

### Target-compute proxy per solved task (TCST)

Until hardware counters are available:

```text
TCST = target_eval_count / solved_task
```

A later implementation may weight batch width, evaluated tokens, bytes read, or measured energy.

## Speculation metrics

- proposal coverage = proposal rounds / attempted rounds;
- proposed_tokens;
- accepted_tokens;
- acceptance_rate = accepted_tokens / proposed_tokens;
- accepted tokens per verified round;
- rejected_at;
- verification_total_us (target decode plus sampling/verification);
- proposer type;
- outcome/fallback counts.

Report distributions, not only means. p50/p95 are useful for acceptance length and verification latency.

## Performance methodology

- run at least one warmup process before measured runs;
- use 3-5 measured repeats;
- rotate mode order between repeats;
- compare median request latency;
- keep server startup time separate from request latency;
- for greedy lossless experiments, record SHA-256 of generated output and compare it with baseline.

## Quality metrics

Every result ultimately needs:

```text
pass | fail | indeterminate
```

For coding tasks also record, when available:

- build result;
- tests passed / failed;
- task-specific assertions.

Never compare a faster failed run with a slower successful run as an optimization win.

## Minimum run metadata

- git commit;
- server executable;
- model identifier/path and quantization when known;
- context size;
- thread count / affinity when relevant;
- backend/device;
- speculative configuration;
- prompt/task id;
- random seed/sampling configuration;
- host identifier (non-personal label is sufficient).
