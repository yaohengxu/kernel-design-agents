# nsys vs ncu: When to Use Which

## TL;DR

| | **nsys** (Nsight Systems) | **ncu** (Nsight Compute) |
|---|---|---|
| **Level** | Application | Kernel |
| **Answers** | **When** and **how** things happen | **Why** a kernel is slow |
| **Timeline** | ✅ Full application timeline | ❌ Single kernel only |
| **CPU view** | ✅ CPU threads, API calls, blocking | ❌ CPU is invisible |
| **GPU view** | ✅ Stream-level, overlap, gaps | ✅ SM-level, stalls, roofline |
| **Overhead** | Low (~1-5%) | High (10-100x slowdown) |
| **Output** | `.nsys-rep` (timeline) | `.ncu-rep` (kernel metrics) |

---

## Use nsys when you want to know:

1. **Is the GPU busy?** — What percentage of time is the GPU actually executing kernels?
2. **Are things overlapping?** — Do kernels from different streams run concurrently? Do memory transfers hide behind compute?
3. **Where are the gaps?** — What causes GPU idle time? CPU blocking? Launch overhead? Sequential transfers?
4. **What's the launch pattern?** — How many kernels are launched? How long does each launch take?
5. **Is the CPU the bottleneck?** — Is one CPU thread saturated launching work?

### Example questions for nsys:
- "为什么 GPU 利用率只有 30%?"
- "CPU 和 GPU 有没有重叠?"
- "为什么有两个 kernel 之间有个大 gap?"
- "内存拷贝和计算有没有并行?"
- "launch overhead 占多少?"

---

## Use ncu when you want to know:

1. **Why is this kernel slow?** — Is it memory-bound, compute-bound, or latency-bound?
2. **What's the bottleneck?** — L1 cache misses? DRAM bandwidth? Warp divergence?
3. **Is the kernel using the hardware well?** — SM occupancy? Tensor core utilization?
4. **What's the roofline position?** — How close to peak throughput?
5. **Which lines of code cause stalls?** — Per-source-line performance attribution.

### Example questions for ncu:
- "这个 kernel 为什么慢?"
- "是 compute-bound 还是 memory-bound?"
- "SM 利用率怎么样?"
- "哪几行代码 stall 最多?"
- "有没有用到 tensor core?"

---

## Workflow: nsys → ncu

The typical optimization workflow uses both tools in sequence:

```
1. nsys profile (application level)
   └─→ Find: "GPU utilization is 45%, kernel_X takes 60% of GPU time"

2. ncu --set full (kernel level)
   └─→ Find: "kernel_X is L2-cache-bound, 80% of time waiting on L1 misses"

3. Fix: restructure memory access pattern

4. nsys profile again
   └─→ Verify: "GPU utilization now 78%, kernel_X takes 40% of GPU time"
```

**Step 1** tells you *where* to look. **Step 2** tells you *why*. **Step 3** is the fix. **Step 4** verifies.

---

## Common mistakes

### Mistake 1: Starting with ncu on an unknown kernel

If you don't know which kernel to optimize, ncu wastes time. Run nsys first to identify the dominant kernel.

### Mistake 2: Using ncu to find overlap issues

ncu profiles one kernel at a time. It can't show you whether kernels from different streams overlap. Use nsys for that.

### Mistake 3: Using nsys to find per-line stalls

nsys doesn't do source-level attribution. It shows *when* a kernel runs, not *why* it's slow. Use ncu with `--set source` for that.

### Mistake 4: Collecting GPU metrics with nsys when you don't need them

`--gpu-metrics-device` adds overhead. If you're only looking at overlap and gaps, skip it. Use it when you need SM occupancy over time.

---

## Feature comparison

| Feature | nsys | ncu |
|---------|------|-----|
| CUDA API trace | ✅ | ❌ |
| Kernel timeline | ✅ | ❌ (one kernel at a time) |
| Stream overlap | ✅ | ❌ |
| CPU thread view | ✅ | ❌ |
| Memory transfer trace | ✅ | ❌ |
| NVTX annotations | ✅ | ✅ |
| SM occupancy (per-kernel) | ❌ | ✅ |
| Memory throughput | ❌ | ✅ |
| Roofline analysis | ❌ | ✅ |
| Per-line stall attribution | ❌ | ✅ |
| Tensor core utilization | ❌ | ✅ |
| Warp divergence | ❌ | ✅ |
| L1/L2 cache analysis | ❌ | ✅ |
| Overhead | Low | High |
