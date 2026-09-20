# Metrics

Raw `tokens/s` remains useful but is not the primary objective.

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

A later implementation may add weighted terms for batch width, evaluated tokens, bytes read, or measured energy.

## Speculation metrics

- proposed_tokens;
- accepted_tokens;
- acceptance_rate = accepted_tokens / proposed_tokens;
- accepted_tokens_per_verification;
- rejected_at;
- verification_ms;
- proposer type;
- fallback count.

Report distributions, not only means (p50/p95 are useful).

## Reuse metrics

- copied/reference-proposed tokens;
- accepted copied tokens;
- accepted copied tokens / generated tokens;
- source kind: current file, repository, prior output, tool schema, external corpus.

## Quality metrics

Every performance result must carry a task result:

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
- model identifier and quantization;
- context size;
- thread count / affinity when relevant;
- backend/device;
- speculative configuration;
- prompt/task id;
- random seed/sampling configuration;
- host identifier (non-personal label is sufficient).
