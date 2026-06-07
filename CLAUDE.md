# Agent Instructions

This repository is the generic Kernel Design Agents workflow reference. It should stay small and task-agnostic.

## Repository Rules

- Use English for repository-facing files, comments, documentation, prompts, and commit messages.
- Keep task-specific prompts, datasets, validators, generated implementations, benchmark logs, and candidate artifacts out of this repository.
- Treat benchmark competitions, including MLSys-style work, as downstream applications of KDA rather than as the scope of this repository.
- Put generated outputs in `runs/`, `outputs/`, or `profile/`; these paths are ignored by git.
- Prefer documenting reusable workflow mechanics over documenting one task's private harness or acceptance thresholds.

## Expected Agent Workflow

For a new task:

1. Create or enter a separate implementation workspace.
2. Define the task objective, constraints, validation command, and promotion criteria.
3. Use `prompts/basic-flow.md` as the starter prompt.
4. Read local task code and documentation before proposing implementation changes.
5. Write the initial plan draft to `docs/draft.md` inside the task workspace.
6. Convert the draft into an executable plan.
7. Implement in small iterations, validating each meaningful candidate.
8. Record candidate relationships, evaluation results, and profiling evidence when applicable.
9. Keep this repository focused on the reusable flow.

## Optional Skills

Use external skills only when they are relevant to the active task:

- `humanize` for plan generation and implementation loops.
- A domain knowledge skill for background research.
- A profiling or report-analysis skill for performance evidence.
- `inference-bench-skill` for LLM inference performance optimization.

## LLM Inference Optimization Rules

When working on LLM inference performance tasks, additionally follow these rules:

- Always benchmark before optimizing. Never guess performance bottlenecks.
- Use `inference-bench-skill` workflow: benchmark → nsys profile → ncu profile → optimize → verify.
- Quantify all performance metrics: tokens/sec, TTFT (ms), ITL (ms), GPU utilization (%), memory bandwidth (GB/s).
- Record baseline and optimized numbers in `benchmark.csv` with exact commands used.
- Each optimization must have profiling evidence (nsys/ncu report citations or metric values).
- Distinguish prefill (compute-bound) from decode (memory-bound) — they require different optimizations.
- Use `prompts/inference-optimize-flow.md` as the starter prompt for inference optimization tasks.
