# nsys Collection Recipes

## Basic trace (always start here)

```bash
nsys profile \
    --trace=cuda,nvtx,osrt,openmp \
    --output=profile/run_name/report \
    ./your_application [args]
```

This captures:
- CUDA API calls and kernel launches
- NVTX annotations (if any)
- OS runtime calls (mutex, condvar, sleep — critical for finding CPU blocking)
- OpenMP parallel regions (if applicable)

---

## With memory tracking

```bash
nsys profile \
    --trace=cuda,nvtx,osrt,openmp \
    --cuda-memory-usage=true \
    --output=profile/run_name/report \
    ./your_application [args]
```

`--cuda-memory-usage=true` adds visibility into `cudaMalloc`, `cudaFree`, `cudaMallocAsync`, `cudaFreeAsync`. Nearly zero overhead — always enable.

---

## With GPU metrics (SM occupancy, etc.)

```bash
nsys profile \
    --trace=cuda,nvtx,osrt,openmp \
    --cuda-memory-usage=true \
    --gpu-metrics-device=0 \
    --output=profile/run_name/report \
    ./your_application [args]
```

`--gpu-metrics-device=0` collects per-SM metrics (occupancy, warps issued, etc.). Adds ~5% overhead. Use when you need to understand SM-level utilization.

---

## Focused capture (only profile a region)

Wrap the region of interest in your code:

```cpp
cudaProfilerStart();
// ... region to profile ...
cudaProfilerStop();
```

Then launch nsys with:

```bash
nsys profile \
    --trace=cuda,nvtx,osrt,openmp \
    --capture-range=cudaProfilerApi \
    --output=profile/run_name/report \
    ./your_application [args]
```

This ignores all activity before `cudaProfilerStart()` and after `cudaProfilerStop()`. Useful for skipping initialization or warmup.

---

## CUDA graph tracing

If the application uses CUDA graphs:

```bash
nsys profile \
    --trace=cuda,nvtx,osrt,openmp \
    --cuda-graph-trace=node \
    --output=profile/run_name/report \
    ./your_application [args]
```

`--cuda-graph-trace=node` breaks graph launches into individual node executions, so you can see each kernel's actual duration rather than one opaque graph launch.

---

## Multi-process tracing

For applications that fork (e.g., data loaders):

```bash
nsys profile \
    --trace=cuda,nvtx,osrt,openmp \
    --capture-range=none \
    --kill=sigterm \
    --output=profile/run_name/report_%p \
    ./your_application [args]
```

`%p` in the output name expands to the PID, so each process gets its own report.

---

## Export formats

After collecting, export for analysis:

```bash
# Export to SQLite (for custom queries)
nsys export --type=sqlite --output=profile/run_name/report.sqlite profile/run_name/report.nsys-rep

# Export to CSV (for nsys stats)
nsys stats --report cuda_api_sum profile/run_name/report.nsys-rep > profile/run_name/stats_cuda_api.csv
nsys stats --report cuda_gpu_kern_sum profile/run_name/report.nsys-rep > profile/run_name/stats_gpu_kern.csv
nsys stats --report cuda_gpu_mem_time_sum profile/run_name/report.nsys-rep > profile/run_name/stats_gpu_mem.csv
```

---

## Directory convention

Follow the same convention as ncu-report-skill:

```
profile/<run_name>/
├── report.nsys-rep          ← raw nsys report
├── report.sqlite            ← exported SQLite (optional)
├── stats/                   ← nsys stats CSV outputs
│   ├── cuda_api_sum.csv
│   ├── cuda_gpu_kern_sum.csv
│   └── cuda_gpu_mem_time_sum.csv
└── analysis/                ← analysis outputs and final report
```
