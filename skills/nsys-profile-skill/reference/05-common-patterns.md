# Common Performance Anti-Patterns

## 1. Sequential memcpy + kernel

**Symptom**: Timeline shows memcpy, kernel, memcpy, kernel — no overlap.

**Cause**: All work on the default stream (stream 0). Default stream serializes everything.

**Fix**: Use separate streams for transfers and compute:

```cpp
cudaStream_t compute_stream, transfer_stream;
cudaStreamCreate(&compute_stream);
cudaStreamCreate(&transfer_stream);

// Overlap: transfer on one stream, compute on another
cudaMemcpyAsync(d_input, h_input, size, cudaMemcpyHostToDevice, transfer_stream);
my_kernel<<<grid, block, 0, compute_stream>>>(d_input, d_output);
cudaMemcpyAsync(h_output, d_output, size, cudaMemcpyDeviceToHost, transfer_stream);

// Use events to synchronize when needed
cudaEvent_t done;
cudaEventCreate(&done);
cudaEventRecord(done, compute_stream);
cudaStreamWaitEvent(transfer_stream, done);  // transfer waits for compute
```

---

## 2. Excessive cudaMalloc/cudaFree

**Symptom**: `nsys stats` shows hundreds of `cudaMalloc` calls. Launch latency spikes.

**Cause**: Allocating GPU memory inside a hot loop or per-batch.

**Fix**: Use a memory pool (e.g., `cudaMallocAsync` with stream-ordered allocation, or a custom pool):

```cpp
// Before (bad):
for (int i = 0; i < N; i++) {
    cudaMalloc(&buf, size);  // expensive!
    kernel<<<...>>>(buf);
    cudaFree(buf);           // expensive!
}

// After (good): cudaMallocAsync with stream ordering
cudaMemPool_t pool;
cudaDeviceGetDefaultMemPool(&pool, 0);
for (int i = 0; i < N; i++) {
    cudaMallocAsync(&buf, size, stream);  // fast, pool-backed
    kernel<<<...>>>(buf);
    cudaFreeAsync(buf, stream);           // fast, deferred
}
```

---

## 3. CPU blocking with cudaDeviceSynchronize

**Symptom**: CPU thread shows large idle gaps. GPU finishes a kernel, then waits for CPU.

**Cause**: `cudaDeviceSynchronize()` called between every kernel launch.

**Fix**: Replace with stream-based synchronization or events:

```cpp
// Before (bad):
kernel_A<<<...>>>();
cudaDeviceSynchronize();  // CPU blocks, GPU waits
process_result();
kernel_B<<<...>>>();

// After (good): launch ahead, sync later
kernel_A<<<..., stream>>>();
kernel_B<<<..., stream>>>();
cudaStreamSynchronize(stream);  // sync once after all launches
process_result();
```

---

## 4. Single-stream bottleneck

**Symptom**: All kernels on stream 0, no concurrency. Timeline shows one long chain.

**Cause**: Not using multiple CUDA streams.

**Fix**: Identify independent work and assign to separate streams:

```cpp
// Independent kernels on different streams
kernel_A<<<..., stream1>>>();
kernel_B<<<..., stream2>>>();
kernel_C<<<..., stream3>>>();

// They can run concurrently if no dependencies
```

---

## 5. Launch overhead dominated by small kernels

**Symptom**: Many tiny kernels (< 10μs each). Launch latency is comparable to kernel execution time.

**Cause**: Fine-grained parallelism with too many small launches.

**Fix**:
1. **Fuse kernels** — combine multiple small kernels into one larger kernel.
2. **Use CUDA graphs** — amortize launch overhead over many executions:

```cpp
cudaGraph_t graph;
cudaGraphExec_t graph_exec;

// Capture the launch sequence once
cudaStreamBeginCapture(stream, cudaStreamCaptureModeGlobal);
kernel_A<<<...>>>();
kernel_B<<<...>>>();
kernel_C<<<...>>>();
cudaStreamEndCapture(stream, &graph);
cudaGraphInstantiate(&graph_exec, graph, NULL, NULL, 0);

// Replay cheaply
cudaGraphLaunch(graph_exec, stream);
```

---

## 6. Implicit synchronization

**Symptom**: GPU has unexpected gaps between kernels. CPU thread shows brief activity between launches.

**Cause**: CUDA API calls that implicitly synchronize:
- `cudaMemcpy` (synchronous version)
- `cudaMalloc` / `cudaFree`
- `cudaDeviceSynchronize`
- Querying default stream status

**Fix**: Use async versions:
- `cudaMemcpyAsync` instead of `cudaMemcpy`
- `cudaMallocAsync` instead of `cudaMalloc`
- `cudaFreeAsync` instead of `cudaFree`
- Stream-ordered operations instead of device sync

---

## 7. PCIe bandwidth saturation

**Symptom**: Transfer time is high. Transfer throughput matches PCIe bandwidth (~64 GB/s for Gen5 x16).

**Cause**: Large data transfers that are bandwidth-limited.

**Fix**:
1. **Reduce transfer size** — use half-precision, quantized types, or transfer only changed data.
2. **Overlap transfers with compute** — see pattern #1.
3. **Use pinned memory** — `cudaMallocHost` for host buffers enables DMA:

```cpp
float *h_data;
cudaMallocHost(&h_data, size);  // pinned memory, faster transfers
```

---

## 8. GPU idle due to load imbalance

**Symptom**: GPU utilization oscillates — busy for a while, then idle, then busy again.

**Cause**: Uneven work distribution across CPU threads or batches.

**Fix**:
1. **Dynamic scheduling** — use a work queue instead of static partitioning.
2. **Increase batch size** — larger batches amortize launch overhead and reduce scheduling gaps.
3. **Prefetch** — launch the next batch while the current one is executing.
