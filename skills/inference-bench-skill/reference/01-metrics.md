# LLM Inference Metrics

## Primary Metrics

### Throughput (tokens/sec)

The most important metric for serving scenarios. Measures how many tokens the system generates per second.

```
Throughput = Total Output Tokens / Total Time (seconds)
```

- **Single-request throughput**: one request at a time, limited by memory bandwidth in decode phase
- **Serving throughput**: many concurrent requests, limited by batch scheduling and GPU utilization

### Time to First Token (TTFT)

Latency from request submission to the first generated token. Dominated by the **prefill phase**.

```
TTFT = Time to complete prefill computation for input tokens
```

- **Interactive use**: <500ms is acceptable, <200ms is good
- **Batch processing**: less critical, but still affects tail latency
- Affected by: input sequence length, prefill kernel efficiency, KV cache allocation

### Inter-Token Latency (ITL)

Time between consecutive tokens during the **decode phase**. Also called "per-token latency".

```
ITL = Time to generate one output token (during autoregressive decoding)
```

- **Interactive use**: <50ms is acceptable, <30ms is good
- **Streaming**: directly affects user-perceived smoothness
- Dominated by: memory bandwidth (loading weights + KV cache), batch size

### End-to-End Latency

Total time from request submission to completion.

```
E2E Latency = TTFT + (ITL × Num Output Tokens)
```

Report P50 (median) and P99 (tail) percentiles.

---

## Secondary Metrics

### GPU Utilization

```
GPU Utilization = Total Kernel Time / Total Wall-Clock Time
```

- >80%: GPU is well-utilized
- <50%: Significant idle time, check CPU scheduling or memory transfers

### Memory Bandwidth Utilization

During decode phase, the bottleneck is almost always memory bandwidth:

```
Bandwidth Utilization = Achieved Bandwidth / Peak Bandwidth (e.g., 800 GB/s on B200)
```

- >70%: Good, close to hardware limit
- <50%: Room for improvement (better batching, quantization)

### KV Cache Utilization

```
KV Cache Usage = Used KV Cache Memory / Allocated KV Cache Memory
```

Low utilization wastes GPU memory that could serve more requests.

### Batch Size

Average number of requests processed simultaneously:

```
Effective Batch Size = Total Requests / Number of Batch Steps
```

Higher batch size → better throughput (up to a point).

---

## Metric Relationships

```
Prefill Phase (compute-bound):
  TTFT ≈ f(input_length, compute_throughput, batch_size)

Decode Phase (memory-bound):
  ITL ≈ f(model_size, quantization, kv_cache_size, batch_size)
  Throughput ≈ batch_size / ITL
```

Key insight: **batch size is the bridge between latency and throughput.** Small batch = low latency, low throughput. Large batch = high latency, high throughput.

---

## Benchmark Output Format

Record results in a standard CSV:

```csv
framework,model,quant,gpu,batch_size,input_len,output_len,tokens_per_sec,ttft_ms,itl_ms,p50_ms,p99_ms
llama.cpp,Qwen2.5-7B,Q4_K_M,RTX5060Ti,1,512,128,45.2,320,22.1,2850,3100
llama.cpp,Qwen2.5-7B,Q4_K_M,RTX5060Ti,8,512,128,180.5,450,44.3,4200,5100
```
