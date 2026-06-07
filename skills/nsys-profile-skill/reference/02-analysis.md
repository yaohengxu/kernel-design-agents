# How to Analyze nsys Reports

## The 30-second check

Open the `.nsys-rep` in nsys-ui. Look at the timeline. In 30 seconds you can answer:

1. **Is the GPU busy?** — Look at the GPU row. Large gaps = GPU idle.
2. **Is the CPU busy?** — Look at the CPU rows. If one CPU thread is launching everything, that's a bottleneck.
3. **Are memory transfers overlapping with kernels?** — Look at the memcpy row vs kernel row. Sequential = bad.
4. **Are kernels from different streams overlapping?** — Multiple streams should show concurrent kernels.

If any of these are obviously wrong, you've found your bottleneck.

---

## CLI-based analysis

### Summary stats

```bash
# Overall GPU utilization
nsys stats --report cuda_gpu_kern_sum profile/run_name/report.nsys-rep

# Memory transfer summary
nsys stats --report cuda_gpu_mem_time_sum profile/run_name/report.nsys-rep

# API call overhead
nsys stats --report cuda_api_sum profile/run_name/report.nsys-rep
```

### Key numbers to extract

| Metric | Where | What it means |
|--------|-------|---------------|
| Kernel time / Total time | `cuda_gpu_kern_sum` | GPU utilization ratio — should be >80% for compute-bound |
| Transfer time / Total time | `cuda_gpu_mem_time_sum` | Memory transfer overhead — should be <10% if overlapping |
| Average launch latency | `cuda_api_sum` (cudaLaunchKernel) | Per-launch overhead — <10μs is good |
| `cudaMalloc` calls | `cuda_api_sum` | Frequent alloc/dealloc = use a pool |

---

## Timeline reading guide

### CPU-GPU overlap

```
CPU Thread 0:  [launch_k1]--------[launch_k2]--------[launch_k3]
GPU Stream 0:       [kernel1_exec]---[kernel2_exec]---[kernel3_exec]
```

**Bad pattern** — CPU waits for each kernel before launching the next. Causes:
- `cudaDeviceSynchronize()` between launches
- Synchronous memcpy between kernels
- Launching from a single CPU thread

**Good pattern** — CPU launches ahead of GPU execution:

```
CPU Thread 0:  [launch_k1][launch_k2][launch_k3]--------[launch_k4][launch_k5]
GPU Stream 0:       [kernel1]---[kernel2]---[kernel3]---[kernel4]---[kernel5]
```

### Multi-stream concurrency

```
GPU Stream 0:  [kernel_A]---[kernel_B]
GPU Stream 1:      [kernel_C]---[kernel_D]
```

This is **good** — kernels from different streams overlap. Requires no dependencies between them.

```
GPU Stream 0:  [kernel_A]---[kernel_B]---[kernel_C]---[kernel_D]
GPU Stream 1:  (empty)
```

This is **bad** — all work is serialized on one stream. Common when code doesn't use multiple streams explicitly.

### Memory transfer overlap

```
GPU:       [memcpy_H2D]---[kernel]---[memcpy_D2H]
```

**Bad** — three sequential operations.

```
GPU:       [memcpy_H2D]
              [kernel (on different stream)]
                         [memcpy_D2H (on different stream)]
```

**Good** — memcpy and kernel overlap on different streams.

---

## nsys-ui tips

1. **Zoom in** — Click and drag on the timeline to zoom into a specific region.
2. **Filter rows** — Right-click to hide/show specific streams or CPU threads.
3. **Select and measure** — Click on a kernel to see its duration, grid/block dimensions.
4. **NVTX ranges** — If your code uses NVTX annotations, they appear as colored ranges on the CPU timeline. Use them to mark phases.
5. **GPU metrics overlay** — If collected, toggle the metrics panel to see SM occupancy over time.
6. **SQLite export** — For complex analysis, export to SQLite and query with SQL. The schema is documented in nsys-ui's help.
