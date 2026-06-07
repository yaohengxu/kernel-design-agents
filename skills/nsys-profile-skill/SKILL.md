---
name: nsys-profile-skill
description: Profile CUDA applications with Nsight Systems (nsys) on NVIDIA GPUs. Use when the user asks to trace a CUDA application, analyze its timeline, find CPU-GPU overlap issues, diagnose kernel launch overhead, memory transfer bottlenecks, or optimize end-to-end application performance — including variants in Chinese ("nsys 分析", "为什么整体慢", "GPU 利用率低").
---

# Skill: CUDA Application Profiling (Nsight Systems)

**When to use:** user asks to profile a CUDA application's overall performance, analyze its execution timeline, find CPU-GPU overlap issues, diagnose kernel launch overhead, or optimize memory transfers. Triggers include: "profile this app", "为什么整体这么慢", "GPU 利用率上不去", "nsys report 说...", "帮我分析一下这份 nsys 报告".

**Target hardware (this repo):** NVIDIA GPUs (generic, with Blackwell B200 notes where applicable).

---

## Golden rule

**Trace → Visualize → Diagnose → Fix, in that order. Never guess.**

Nsight Systems gives you the **application-level** view: how kernels, memory transfers, and CPU work overlap (or don't). Most performance issues are visible in the timeline within 30 seconds of opening the report. Don't invent hypotheses before you have the trace.

---

## Quickstart (what to do when someone says "profile this app")

1. **Decide what you're profiling.** What inputs? What's the target metric — throughput, latency, GPU utilization? If the application has variable workloads, pick representative scenarios.

2. **Run nsys with the right collection flags.** See [`reference/01-collection.md`](reference/01-collection.md). Key options:
   - `nsys profile --trace=cuda,nvtx,osrt,openmp` — standard trace
   - `--cuda-memory-usage=true` — track memory allocations
   - `--gpu-metrics-device=0` — collect GPU metrics (SM occupancy, etc.)
   - `--capture-range=cudaProfilerApi` — focus on a specific region

3. **Analyze the timeline in nsys-ui or with the CLI.** See [`reference/02-analysis.md`](reference/02-analysis.md). Look for:
   - CPU-GPU gaps (launch overhead)
   - Sequential memory transfers (missing overlap)
   - Kernel serialization (should be concurrent)
   - Idle periods (dependency or scheduling issues)

4. **Quantify bottlenecks.** See [`reference/03-metrics.md`](reference/03-metrics.md). Use `nsys stats` for summary numbers: kernel time占比, transfer time占比, API call overhead.

5. **Write the report** with evidence-backed recommendations, ranked by expected impact. See [`reference/04-report-template.md`](reference/04-report-template.md).

---

## File index

### Reference docs

| File | Purpose |
|---|---|
| [`reference/01-collection.md`](reference/01-collection.md) | nsys command recipes: basic trace, GPU metrics, memory tracking, focused capture |
| [`reference/02-analysis.md`](reference/02-analysis.md) | How to read the timeline, identify bottlenecks, use nsys-ui and CLI |
| [`reference/03-metrics.md`](reference/03-metrics.md) | Key metrics: SM occupancy, memory bandwidth, kernel overlap, launch latency |
| [`reference/04-report-template.md`](reference/04-report-template.md) | How to structure the final profiling report |
| [`reference/05-common-patterns.md`](reference/05-common-patterns.md) | Common performance anti-patterns and their fixes |
| [`reference/06-nsys-vs-ncu.md`](reference/06-nsys-vs-ncu.md) | When to use nsys vs ncu — they solve different problems |

### Helpers

| File | Purpose |
|---|---|
| [`helpers/parse_nsys_stats.py`](helpers/parse_nsys_stats.py) | Parse `nsys stats` CSV output, extract key ratios |
| [`helpers/timeline_summary.py`](helpers/timeline_summary.py) | Generate ASCII timeline summary from nsys-rep |
| [`helpers/compare_runs.py`](helpers/compare_runs.py) | Side-by-side comparison of two profiling runs |

---

## Critical lessons (don't skip)

1. **nsys and ncu are complementary, not interchangeable.** nsys shows **when** things happen (timeline, overlap, gaps); ncu shows **why** a kernel is slow (memory stalls, occupancy, roofline). Use nsys first to find the bottleneck, then ncu to drill into a specific kernel.

2. **Always trace `osrt` (OS runtime) calls.** Without it, you can't see CPU-side blocking (mutex, condvar, sleep) that causes GPU idle time. Add `--trace=osrt` by default.

3. **CUDA graphs hide launch overhead — but not always.** If the user is using CUDA graphs, nsys shows the graph launch as one unit. You need `--cuda-graph-trace=node` to see individual node execution.

4. **GPU metrics collection has overhead.** `--gpu-metrics-device` adds ~5% overhead. Don't use it for latency-critical traces unless you need SM-level data.

5. **Multi-stream concurrency is easy to miss in CLI output.** Always open the `.nsys-rep` in nsys-ui to visually confirm whether kernels from different streams actually overlap. The timeline view is the source of truth.

6. **Memory allocation tracking requires `--cuda-memory-usage=true`.** Without it, `cudaMalloc`/`cudaFree` are invisible. This flag is cheap — always enable it.

---

## Related skills

- [`ncu-report-skill`](../ncu-report-skill/) — Per-kernel profiling with Nsight Compute. Use it after nsys identifies which kernel to optimize.
- [`KernelWiki`](../KernelWiki/) — Kernel design knowledge base for implementing fixes.
