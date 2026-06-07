# Bottleneck Playbook

Pattern → Cause → Fix for common LLM inference bottlenecks.

---

## 1. Decode is Memory-Bandwidth Bound

**Symptom**: ITL scales linearly with model size (bytes). ITL improves with quantization.

**Evidence**: `dram__bytes_read.sum` near peak bandwidth. `long_scoreboard` stalls dominate.

**Cause**: Each decode step loads all model weights + KV cache from HBM. With batch_size=1, arithmetic intensity is very low.

**Fix**:
1. **Quantization** — Q4_K_M reduces weight bytes by ~4x. Most impactful single change.
2. **Increase batch size** — amortize weight loading across multiple requests.
3. **KV cache quantization** — reduce KV cache memory traffic.

---

## 2. Prefill is Compute-Bound

**Symptom**: TTFT scales quadratically with input length. Flash attention doesn't help enough.

**Evidence**: High `sm__throughput.avg.pct_of_peak_sustained_elapsed`. Compute pipeline is saturated.

**Cause**: Prefill processes all input tokens in parallel. Attention computation is O(n²).

**Fix**:
1. **Flash Attention** — reduces memory access pattern, enables tiling.
2. **Chunked prefill** — split long prompts into chunks to interleave with decode.
3. **Tensor parallelism** — split across multiple GPUs for large models.

---

## 3. Low SM Occupancy

**Symptom**: GPU metrics show low occupancy (<30%). Many SMs are idle.

**Evidence**: `sm__warps_active.avg.pct_of_peak_sustained_elapsed` is low.

**Cause**: Small batch size (decode), high register usage per thread, or small grid dimensions.

**Fix**:
1. **Increase batch size** — more requests = more parallel work.
2. **Reduce register pressure** — use `__launch_bounds__` to limit registers.
3. **Persistent kernels** — keep kernels running across multiple invocations.

---

## 4. High Launch Overhead

**Symptom**: Many small kernels (<10μs each). nsys shows gaps between kernels.

**Evidence**: `cudaLaunchKernel` API time is significant fraction of total.

**Cause**: LLM inference launches hundreds of small kernels per token (matmul, layernorm, residual, activation).

**Fix**:
1. **Kernel fusion** — combine consecutive small kernels (e.g., RMSNorm + residual add).
2. **CUDA graphs** — capture the kernel launch sequence and replay it.
3. **Custom fused kernels** — write fused kernels for common patterns.

---

## 5. KV Cache Memory Pressure

**Symptom**: OOM at moderate batch sizes. GPU memory is full but utilization is low.

**Evidence**: `cudaMalloc` failures. KV cache consumes most of GPU memory.

**Cause**: Each request allocates KV cache proportional to sequence length × num_layers × hidden_dim.

**Fix**:
1. **PagedAttention** (vLLM) — allocate KV cache in fixed-size pages, share across requests.
2. **KV cache quantization** — store KV cache in INT8 or FP8.
3. **Sliding window** — limit attention window to recent tokens.
4. **Prefix caching** — share KV cache for common prefixes.

---

## 6. CPU Scheduling Bottleneck

**Symptom**: GPU utilization is low despite pending requests. nsys shows CPU thread is busy.

**Evidence**: Large CPU-GPU gaps in nsys timeline. CPU thread spends time in scheduler code.

**Cause**: CPU-bound scheduling logic (beam search, continuous batching) doesn't overlap with GPU execution.

**Fix**:
1. **Async scheduling** — move scheduling to a separate CPU thread.
2. **Overlap prefill/decode** — schedule decode while prefill is running.
3. **Simplify scheduling** — reduce complex sampling logic on CPU.

---

## 7. Context Switching Overhead

**Symptom**: Throughplate drops with long sequence requests mixed with short ones.

**Evidence**: High variance in ITL. nsys shows frequent context switches between different request phases.

**Cause**: Long prefill blocks short decode requests. No priority scheduling.

**Fix**:
1. **Chunked prefill** — break long prefill into small chunks interleaved with decode.
2. **Priority scheduling** — prioritize decode (latency-sensitive) over prefill.
3. **Separate prefill/decode** — use different GPUs or streams for each phase (DistServe).

---

## 8. Quantization Quality vs Speed Tradeoff

**Symptom**: Quantized model is fast but output quality is poor.

**Evidence**: Benchmark shows good throughput but quality metrics (perplexity, accuracy) degrade.

**Cause**: Aggressive quantization (Q2, Q3) loses too much precision.

**Fix**:
1. **Use Q4_K_M** — best quality/speed tradeoff for most models.
2. **GPTQ/AWQ** — better quality than naive quantization at same bits.
3. **Mixed precision** — quantize linear layers but keep attention in higher precision.
4. **Activation-aware quantization** — AWQ preserves important weights.

---

## Quick Reference

| Bottleneck | Primary Signal | Primary Fix |
|-----------|---------------|-------------|
| Decode bandwidth | ITL ∝ model_bytes | Quantization (Q4) |
| Prefill compute | TTFT ∝ seq_len² | FlashAttention |
| Low occupancy | SM% < 30% | Increase batch |
| Launch overhead | Many small kernels | CUDA graphs / fusion |
| KV cache memory | OOM at low batch | PagedAttention |
| CPU scheduling | GPU idle, CPU busy | Async scheduling |
| Context switching | High ITL variance | Chunked prefill |
| Quantization quality | Quality drop | Q4_K_M or AWQ |
