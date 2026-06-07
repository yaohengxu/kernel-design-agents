# Agent Flow

Kernel Design Agents is a repeatable loop for agent-driven implementation work. The loop is useful when a task needs both exploration and evidence-based promotion decisions.

## Principle

Keep the reusable workflow separate from the task workspace. This repository explains the flow. The task workspace owns code, tests, datasets, benchmark scripts, private rules, and generated artifacts.

MLSys-style benchmark work is one possible application of this loop. The same flow can also be used for compiler passes, runtime kernels, infrastructure changes, or other performance-sensitive tasks.

## Minimal Loop

1. Define the task contract.
2. Let the agent inspect the local workspace.
3. Make the agent write `docs/draft.md`.
4. Convert the draft into an executable plan.
5. Implement the first candidate.
6. Validate correctness.
7. Measure the target metric when applicable.
8. Record evidence and decide whether to keep, revise, or reject the candidate.
9. Repeat until the promotion criteria are met or the remaining blockers are explicit.

## Task Contract

Each task should state:

- Objective.
- Inputs and outputs.
- Correctness requirements.
- Constraints on implementation language, dependencies, APIs, or deployment.
- Validation command.
- Evaluation command, if different from validation.
- Promotion criteria.

## Evidence Records

Use simple files in the task workspace:

- `docs/draft.md` for the first plan draft.
- `docs/plan.md` for the executable plan.
- `benchmark.csv` or another tabular log for measurable results.
- `candidates.jsonl` for candidate names, parent links, and status.
- `profile/` for profiler output or report summaries.
- `runs/` or `outputs/` for generated artifacts.

The exact format is less important than consistency. A future reader should be able to reconstruct what changed, what was measured, and why a candidate was promoted.

## Promotion Rule

Promote a candidate only when it satisfies the task contract and has evidence that it improves or preserves the target metric. If a candidate is rejected, record the reason instead of silently discarding it.

---

## LLM Inference Optimization Variant

For LLM inference performance tasks, the loop specializes to:

1. **Baseline benchmark** — run the framework's benchmark tool, record tokens/sec, TTFT, ITL.
2. **nsys profile** — trace the inference run, identify Top-3 kernels by wall-clock time.
3. **ncu profile** — deep-dive into the top kernel, classify as memory/compute/latency-bound.
4. **Optimize** — apply targeted fix (quantization, FlashAttention, batch tuning, kernel fusion).
5. **Re-benchmark** — compare with baseline, record in `benchmark.csv`.
6. **Promote or iterate** — if target met, promote. Otherwise, profile again for the next bottleneck.

Use `prompts/inference-optimize-flow.md` as the starter prompt. Use `inference-bench-skill` for profiling and analysis tools.
