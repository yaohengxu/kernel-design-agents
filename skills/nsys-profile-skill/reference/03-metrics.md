# Key nsys Metrics

## Application-level metrics

### GPU utilization

```
GPU Utilization = Total Kernel Time / Total Wall-clock Time
```

- **>80%**: GPU is well-utilized. Look at per-kernel efficiency instead.
- **50-80%**: Significant gaps. Check for launch overhead, sequential transfers, CPU blocking.
- **<50%**: Major bottleneck. The GPU is idle more than half the time.

### Kernel time ratio

```
Kernel Ratio = Sum of all kernel durations / Total GPU active time
```

If this is low, the GPU spends more time on memory transfers than compute.

### Transfer time ratio

```
Transfer Ratio = Sum of all memcpy durations / Total GPU active time
```

- **<10%**: Transfers are not a bottleneck.
- **10-30%**: Significant. Consider overlapping transfers with compute.
- **>30%**: Major bottleneck. Likely the dominant issue.

---

## Launch overhead metrics

### Average launch latency

```
Avg Launch Latency = cudaLaunchKernel total time / number of launches
```

- **<5μs**: Excellent. CUDA graphs or efficient launch path.
- **5-20μs**: Normal for non-graph launches.
- **20-100μs**: High. Check for driver overhead, frequent synchronization.
- **>100μs**: Extreme. Likely a driver issue or excessive API calls.

### Launches per second

```
Launch Rate = Number of kernel launches / Total time
```

- **>10,000/s**: Fine-grained launches. Consider CUDA graphs.
- **1,000-10,000/s**: Normal workload.
- **<1000/s**: Large kernels, launch overhead is negligible.

---

## Memory metrics

### Transfer size

```
Total Transfer Bytes = Sum of all memcpy bytes (H2D + D2H + D2D + H2H)
```

### Transfer throughput

```
Transfer Throughput = Total Transfer Bytes / Total Transfer Time
```

Compare with theoretical bandwidth:
- PCIe Gen5 x16: ~64 GB/s
- NVLink (B200): ~900 GB/s per link
- If throughput << theoretical, transfers are small and latency-dominated.

### Allocation overhead

```
Alloc Count = Number of cudaMalloc calls
Free Count = Number of cudaFree calls
```

Frequent alloc/free (hundreds per second) indicates a memory pool should be used.

---

## GPU metrics (requires --gpu-metrics-device)

### SM Occupancy

```
SM Occupancy = Active warps / Maximum warps per SM
```

- **>70%**: Good occupancy. Kernel has enough parallelism.
- **30-70%**: Moderate. May benefit from occupancy tuning.
- **<30%**: Low. Kernel likely has high register usage or small grid.

### SM Activity

```
SM Activity = SMs with at least one active warp / Total SMs
```

- **100%**: All SMs are utilized.
- **<100%**: Grid is too small to fill the GPU. Common with small batch sizes.

### Warp Execution Efficiency

```
Warp Exec Efficiency = Active warps / Issued warps
```

- **>80%**: Good. Warps are doing useful work.
- **<80%**: Significant warp divergence or stalls.

---

## Derived metrics (compute from raw data)

### Overlap efficiency

```
Overlap Efficiency = (Kernel Time + Transfer Time - Total Time) / min(Kernel Time, Transfer Time)
```

- **0%**: No overlap. Sequential execution.
- **>50%**: Good overlap. Transfers hide behind compute.

### Stream utilization

```
Stream Utilization = Active streams / Available streams
```

If you have N streams but only 1 is ever active, you're not getting concurrency.

### API overhead ratio

```
API Overhead = Total API time / Total wall-clock time
```

- **<5%**: Negligible.
- **5-20%**: Noticeable. Consider reducing API calls.
- **>20%**: Major bottleneck. Likely excessive synchronization or allocation.
