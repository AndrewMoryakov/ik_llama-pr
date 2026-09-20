# Trace Format

Runtime speculative tracing is enabled only when the environment variable `IK_LLAMA_SPEC_TRACE` points to a file.

The file format is **NDJSON**: one independent JSON object per line.

## Why NDJSON

- streaming-friendly;
- append-only;
- readable while the process is running;
- partial traces remain useful after crashes;
- easy to process with standard tools.

A killed process may leave a malformed final line. The project summarizer ignores only a malformed final line; malformed earlier records are treated as errors.

## Record schema

The canonical machine-readable schema is:

`experiments/semantic-decoding/trace.schema.json`

Example:

```json
{"schema_version":1,"type":"speculation","outcome":"partial_accept","seq_id":0,"n_past":512,"proposer":"suffix","proposed_tokens":12,"accepted_tokens":8,"rejected_at":8,"verification_total_us":7421,"used_speculative":true,"failed":false}
```

## Fields

- `schema_version` — trace record schema version.
- `type` — currently `speculation`.
- `outcome` — lifecycle result for this speculative attempt.
- `seq_id` — llama sequence id.
- `n_past` — target position at the beginning of the round.
- `proposer` — speculative implementation selected for the round.
- `proposed_tokens` — candidate draft token count.
- `accepted_tokens` — accepted draft prefix length.
- `rejected_at` — zero-based first rejected draft position, or `null` if no draft token was rejected.
- `verification_total_us` — target verification decode plus sampling/verification time.
- `used_speculative` — whether speculative ids were committed into the result.
- `failed` — whether the round failed.

## Outcomes

Current values:

- `no_proposal`
- `below_min_draft`
- `checkpoint_unavailable`
- `proposal_invalid`
- `verify_failed`
- `sampling_failed`
- `partial_accept`
- `full_accept`

The in-memory round result may temporarily use internal states not serialized as stable public trace outcomes.

## Important metric distinction

**Proposal coverage** and **acceptance rate** measure different things.

```text
proposal coverage = proposal rounds / attempted rounds
acceptance rate   = accepted draft tokens / proposed draft tokens
```

A proposer with very high acceptance but very low proposal coverage may still have little practical impact.

## Performance warning

The current trace sink performs file I/O. Therefore trace-enabled wall-clock timings are diagnostic only.

Use the benchmark runner's normal performance pass for latency comparisons and `--trace-pass` only for behavior analysis.
