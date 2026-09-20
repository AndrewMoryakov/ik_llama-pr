# Benchmark Result Record

Use this template for the first real CPU measurements.

## Run identity

- Date/time:
- Git commit:
- Host label:
- CPU:
- RAM configuration:
- OS:
- Build type:
- Compiler:
- Model:
- Quantization:
- Model file size:
- Threads:
- Context size:
- n_predict:
- Additional server arguments:

## Prompt / task

- Task id:
- Prompt file:
- Workload type: synthetic / coding / agentic
- Deterministic greedy run: yes / no

## Performance

| Mode | Median request (s) | Min | Max | Speedup vs baseline | Output equal |
| --- | ---: | ---: | ---: | ---: | :---: |
| baseline | | | | 1.000x | |
| ngram-mod | | | | | |
| suffix | | | | | |

## Trace diagnostics

| Mode | Proposal coverage | Acceptance rate | Proposed tokens | Accepted tokens | Verified rounds |
| --- | ---: | ---: | ---: | ---: | ---: |
| ngram-mod | | | | | |
| suffix | | | | | |

## Correctness / quality

- Baseline output hash:
- ngram output hash:
- suffix output hash:
- Outputs byte-identical:
- Build/test result if coding task:
- Manual notes:

## Interpretation

Record observations only after separating performance-pass numbers from traced-pass diagnostics.

Questions to answer:

1. Which proposer reduces end-to-end request time?
2. Is the gain explained by proposal coverage, acceptance length, or both?
3. Does verification overhead erase part of the benefit?
4. Are outputs identical under deterministic settings?
5. Is the result stable across repeated runs?
6. Which failure/fallback outcomes dominate?
