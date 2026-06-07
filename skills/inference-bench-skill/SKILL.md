---
name: inference-bench-skill
description: Profile and optimize LLM inference performance on NVIDIA GPUs. Use when the user asks to benchmark an inference framework, analyze throughput/latency bottlenecks, optimize tokens/sec or time-to-first-token, profile llama.cpp/vLLM/TensorRT-LLM, or diagnose why inference is slow — including variants in Chinese ("推理优化", "为什么推理慢", "tokens/s 上不去", "TTFT 太高", "推理 benchmark").
---

# Skill: LLM Inference Performance Optimization

**When to use:** user asks to benchmark or optimize LLM inference throughput/latency, profile inference frameworks, find bottlenecks in the inference pipeline, or improve tokens/sec, TTFT, ITL. Triggers include: "推理优化", "为什么推理慢", "tokens/s 上不去", "benchmark 一下", "TTFT 太高", "优化推理性能".

**Target frameworks:** llama.cpp, vLLM, TensorRT-LLM, SGLang, and custom inference pipelines.

---

## Golden rule

**Benchmark → Profile → Diagnose → Optimize → Verify, in that order. Never guess.**

Most inference performance issues are dominated by 1-3 kernels that nsys can identify in 30 seconds. Don't hypothesize before you have the trace. Don't start optimizing before you've quantified the baseline and identified the bottleneck.

---

## Core Metrics

| Metric | Definition | Target (depends on model/hardware) |
|--------|-----------|-----------------------------------|
| **Throughput** | tokens/sec (total output tokens / total time) | Maximize |
| **TTFT** | Time to First Token (prefill latency) | Minimize, <500ms for interactive |
| **ITL** | Inter-Token Latency (per-token decode time) | Minimize, <50ms for interactive |
| **P50/P99 Latency** | Median and tail latency per request | Minimize variance |
| **GPU Utilization** | % of time GPU is executing kernels | >80% |
| **Memory Bandwidth** | GB/s during decode phase | Near peak (e.g., >800 GB/s on B200) |

---

## Quickstart: Five-Phase Workflow

### Phase 1: Baseline Benchmark

Run the framework's built-in benchmark to establish baseline numbers.

```bash
# llama.cpp
./llama-bench -m model.gguf -p 512 -n 128 -r 3

# vLLM
python -m vllm.entrypoints.openai.api_server --model <model> &
python benchmark_serving.py --backend openai --model <model> --num-prompts 100

# TensorRT-LLM
trtllm-bench --model <model> --throughput --max-batch-size 32
```

Record: tokens/sec, TTFT, ITL, batch size, quantization, GPU model.

See [`reference/02-benchmark-tools.md`](reference/02-benchmark-tools.md).

### Phase 2: Application-Level Profiling (nsys)

Trace the entire inference run to find which kernels dominate wall-clock time.

```bash
nsys profile --trace=cuda,nvtx,osrt --cuda-memory-usage=true \
    --output=profile/run_name/report \
    ./llama-cli -m model.gguf -p 512 -n 128 ...
```

Look for:
- Top-3 kernels by total time
- CPU-GPU gaps (launch overhead)
- Memory transfer bottlenecks
- Stream utilization

See [`reference/03-profiling-workflow.md`](reference/03-profiling-workflow.md).

### Phase 3: Kernel-Level Profiling (ncu)

For each Top-N bottleneck kernel, run Nsight Compute to understand *why* it's slow.

```bash
ncu --set full --section SourceCounters \
    --kernel-name "flash_attention" \
    --launch-skip 10 --launch-count 3 \
    -o profile/run_name/ncu_flash_attn \
    ./llama-cli -m model.gguf -p 512 -n 8 ...
```

Classify each kernel:
- **Memory-bound**: low compute/byte ratio, high DRAM traffic
- **Compute-bound**: high arithmetic intensity, near roofline
- **Latency-bound**: low occupancy, high stall counts
- **Launch-bound**: kernel is fast but launch overhead dominates

See [`reference/04-bottleneck-playbook.md`](reference/04-bottleneck-playbook.md).

### Phase 4: Optimize

Based on the bottleneck type, select optimization strategies:

| Bottleneck | Optimization |
|-----------|-------------|
| Memory-bound decode | Quantization (Q4_K_M, Q8_0, GPTQ, AWQ) |
| Memory-bound prefill | FlashAttention, paged KV cache |
| Low occupancy | Increase batch size, reduce register pressure |
| Launch overhead | CUDA graphs, kernel fusion |
| CPU scheduling | Async scheduling, continuous batching |
| KV cache | PagedAttention, KV cache quantization |

Implement → benchmark → compare with baseline.

See [`reference/06-optimization-catalog.md`](reference/06-optimization-catalog.md).

### Phase 5: Report

Write a report with:
- Baseline vs optimized numbers (table)
- Profiling evidence (nsys/ncu screenshots or metric values)
- What was changed and why
- Remaining bottlenecks and next steps

---

## File Index

### Reference docs

| File | Purpose |
|---|---|
| [`reference/01-metrics.md`](reference/01-metrics.md) | LLM inference metrics: throughput, TTFT, ITL, GPU utilization |
| [`reference/02-benchmark-tools.md`](reference/02-benchmark-tools.md) | Benchmark tools for llama.cpp, vLLM, TensorRT-LLM, SGLang |
| [`reference/03-profiling-workflow.md`](reference/03-profiling-workflow.md) | nsys→ncu two-stage profiling workflow |
| [`reference/04-bottleneck-playbook.md`](reference/04-bottleneck-playbook.md) | Bottleneck pattern → cause → fix |
| [`reference/05-framework-guide.md`](reference/05-framework-guide.md) | Framework-specific tips: llama.cpp, vLLM, TRT-LLM, SGLang |
| [`reference/06-optimization-catalog.md`](reference/06-optimization-catalog.md) | Optimization techniques: quantization, batch, kernel fusion, etc. |

### Helpers

| File | Purpose |
|---|---|
| [`helpers/parse_llama_bench.py`](helpers/parse_llama_bench.py) | Parse llama-bench output, extract throughput/latency |
| [`helpers/parse_vllm_bench.py`](helpers/parse_vllm_bench.py) | Parse vLLM benchmark_serving output |
| [`helpers/bottleneck_rank.py`](helpers/bottleneck_rank.py) | Rank bottleneck kernels from nsys/ncu reports |

---

## Critical Lessons

1. **Decode is bandwidth-bound, prefill is compute-bound.** These are fundamentally different phases. Optimizing decode means maximizing memory bandwidth utilization. Optimizing prefill means maximizing compute throughput. Don't confuse them.

2. **Batch size is the #1 lever for throughput.** Single-request latency is limited by memory bandwidth. Throughput comes from batching many requests together (amortizing kernel launch overhead and improving memory access patterns).

3. **Quantization is the #1 lever for memory-bound decode.** Q4_K_M reduces memory traffic by ~4x vs FP16, directly improving decode tokens/sec on bandwidth-limited GPUs.

4. **Always benchmark with the right granularity.** Use `llama-bench` for single-request latency, `benchmark_serving.py` for serving throughput under concurrent load. They measure different things.

5. **nsys first, ncu second.** nsys tells you *which* kernel to optimize. ncu tells you *why*. Don't skip nsys and jump to ncu — you might optimize a kernel that contributes only 5% of total time.

6. **Profile the actual workload, not synthetic inputs.** Real prompts have variable lengths. Profile with representative input distributions, not just fixed-length synthetic data.

---

## Related Skills

- [`ncu-report-skill`](../ncu-report-skill/) — Deep kernel-level profiling with Nsight Compute.
- [`nsys-profile-skill`](../nsys-profile-skill/) — Application-level timeline profiling with Nsight Systems.
- [`KernelWiki`](../KernelWiki/) — Blackwell/Hopper kernel optimization knowledge base.
