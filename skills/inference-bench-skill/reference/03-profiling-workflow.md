# Profiling Workflow: nsys → ncu

## Overview

LLM inference profiling follows a two-stage approach:

1. **nsys** (Nsight Systems) — Application-level: find *which* kernel to optimize
2. **ncu** (Nsight Compute) — Kernel-level: understand *why* it's slow

```
nsys trace → Top-N kernels → ncu each → bottleneck type → optimization
```

---

## Stage 1: nsys — Find the Bottleneck Kernel

### Collection

```bash
nsys profile \
    --trace=cuda,nvtx,osrt \
    --cuda-memory-usage=true \
    --output=profile/run_name/report \
    ./llama-cli -m model.gguf -p 512 -n 128
```

For vLLM/TRT-LLM (attach to running process):

```bash
nsys profile \
    --trace=cuda,nvtx,osrt \
    --cuda-memory-usage=true \
    --capture-range=cudaProfilerApi \
    --output=profile/run_name/report \
    python your_inference_script.py
```

### Analysis

```bash
# Export stats
nsys stats --report cuda_gpu_kern_sum profile/run_name/report.nsys-rep > stats/kern.csv
nsys stats --report cuda_gpu_mem_time_sum profile/run_name/report.nsys-rep > stats/mem.csv
nsys stats --report cuda_api_sum profile/run_name/report.nsys-rep > stats/api.csv

# Parse with helper
python helpers/parse_nsys_stats.py --stats-dir stats/ --output analysis/summary.md
```

### What to Look For

| Finding | Implication |
|---------|------------|
| One kernel takes >50% of GPU time | That's your optimization target |
| Large gaps between kernels | CPU scheduling bottleneck or sync overhead |
| Sequential memcpy + kernel | Missing overlap, use streams |
| Many small kernels (<10μs each) | Launch overhead, consider fusion or CUDA graphs |

### Typical LLM Inference Kernel Hierarchy

```
Prefill Phase:
  flash_attention_fwd > gemm (QKV projection) > layernorm > residual_add

Decode Phase:
  flash_attention_fwd (with KV cache) > gemm (small batch) > rmsnorm
```

For decode, attention with KV cache loading is usually the #1 bottleneck.

---

## Stage 2: ncu — Deep Kernel Analysis

### Collection

For a specific kernel identified by nsys:

```bash
ncu --set full \
    --section SourceCounters \
    --kernel-name "flash_attention" \
    --launch-skip 10 --launch-count 3 \
    -o profile/run_name/ncu_flash_attn \
    ./llama-cli -m model.gguf -p 512 -n 8
```

Flags:
- `--kernel-name "regex"`: filter to specific kernel
- `--launch-skip N`: skip first N launches (warmup)
- `--launch-count N`: only profile N launches
- `--set full`: collect all metrics
- `--section SourceCounters`: per-line attribution

### Classification

| Type | Indicator | Optimization |
|------|-----------|-------------|
| **Memory-bound** | Low compute/byte ratio, high DRAM traffic, `long_scoreboard` stalls dominate | Quantization, reduce data movement |
| **Compute-bound** | High arithmetic intensity, near roofline, `mio_*` stalls | Algorithmic improvement, tensor cores |
| **Latency-bound** | Low occupancy, high register usage, small grid | Increase batch, reduce registers |
| **Launch-bound** | Kernel is fast (<10μs), many launches | CUDA graphs, kernel fusion |

### Using the Helper

```bash
python helpers/bottleneck_rank.py \
    --nsys-stats stats/kern.csv \
    --ncu-report profile/run_name/ncu_flash_attn.ncu-rep \
    --output analysis/bottlenecks.md
```

---

## Quick Decision Tree

```
Is throughput low?
├─ Yes → Check batch size → Increase batch → Re-benchmark
└─ No → Is TTFT high?
   ├─ Yes → Prefill slow → Profile prefill kernels → FlashAttention? Quantize?
   └─ No → Is ITL high?
      ├─ Yes → Decode slow → Profile decode kernels → Memory-bound? → Quantize
      └─ No → Tail latency → Check scheduling, context switching
```
