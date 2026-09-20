# Hypotheses

Each hypothesis must be falsifiable and evaluated against the same task set and model configuration.

## H1 — self-speculation reduces sequential target work
Suffix and/or n-gram speculation reduce target evaluation steps and wall time on real coding-agent trajectories without changing target-model semantics.

Primary measures:
- target evaluations / solved task;
- accepted tokens / verification;
- wall time / solved task.

## H2 — repository text is a strong code proposer
A repository-span proposer can predict a meaningful fraction of generated code/tool text because agent outputs reuse signatures, paths, syntax, boilerplate, and existing source.

Primary measures:
- proposal hit rate;
- accepted repo-copy tokens / generated tokens;
- verification efficiency.

## H3 — semantic routing beats a fixed proposer
A cheap router selecting among suffix, n-gram, repo-copy, and normal decode yields lower target compute per solved task than any single proposer across a mixed workload.

The router must not use a target forward pass merely to decide whether to avoid one.

## H4 — compact reasoning lowers task latency
A constrained agent protocol (for example OBS/HYP/READ/ACT/VERIFY) reduces generated reasoning tokens while preserving coding-task success within an agreed tolerance.

This is quality-changing unless verified otherwise and must be reported separately from lossless decoding experiments.

## H5 — compact action IR removes redundant generation
Reference-based actions such as READ, COPY, REPLACE, PATCH, TEST, and symbol/span references reduce output token count compared with regenerating unchanged text.

## H6 — verbosity can be steered without full fine-tuning
Activation/control-vector steering may move a model toward concise reasoning while retaining task success. This is a later experiment and must be isolated from baseline inference changes.

## Non-goal

Randomly dropping BPE tokens after generation is not expected to accelerate autoregressive decoding: later tokens depend on the skipped token's state. The project instead attacks redundant sequential computation, redundant representation, and redundant protocol text.
