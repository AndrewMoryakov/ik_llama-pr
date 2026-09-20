# ik_llama speculative code map

This note records the existing hooks we should reuse before adding new counters.

## Core

### `common/speculative.h`

Already exposes:

- `common_speculative_draft_result` — proposal tokens, proposal distributions, proposer type, target-only flag.
- `common_speculative_metrics_stage_snapshot` — per-stage counters:
  - begin/draft/accept calls;
  - generated/accepted drafts;
  - generated/accepted tokens;
  - drafted/accepted counts by speculative position;
  - begin/draft/accept timings.
- `common_speculative_metrics_snapshot`.
- `common_speculative_get_metrics_snapshot(...)`.
- `common_speculative_round_result` and `common_speculative_run_round(...)`.

### `common/speculative.cpp`

Important lifecycle points:

1. `common_speculative_draft(...)`
   - selects the first stage that produces a usable draft;
   - records generated draft/token counters;
   - records drafted positions.

2. `common_speculative_accept(...)`
   - receives the accepted-prefix length;
   - records accepted draft/token counters;
   - records accepted positions;
   - already feeds the autotuner.

3. `common_speculative_run_round(...)`
   - owns one complete propose -> target verify -> commit/restore round;
   - best candidate for **per-round** experimental tracing because it knows the draft and final accepted ids.

4. `common_speculative_print_stats(...)`
   - emits aggregate stage statistics at request end.

## Server integration

### `examples/server/server-context.cpp`

The server already invokes `common_speculative_print_stats(...)` from slot timing/stat reporting.

This means the first benchmark can use aggregate statistics without modifying the target decode path.

## M1 implementation choice

Do **not** introduce duplicate counters.

Add an opt-in experimental trace sink around `common_speculative_run_round(...)` (or its server call site) only for data that aggregate snapshots cannot express:

- per-round proposer;
- proposed token count;
- accepted-prefix length;
- rejection position;
- target verification duration;
- request/task correlation id.

Keep normal builds and runtime behavior unchanged when tracing is disabled.

## Later proposer work

A repository-copy proposer should integrate through the existing speculative abstraction rather than create a second verification path. Its first version should produce ordinary `llama_tokens` and reuse target verification/commit semantics.
