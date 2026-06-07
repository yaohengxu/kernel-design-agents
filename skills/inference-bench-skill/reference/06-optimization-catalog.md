# Optimization Catalog

Techniques for improving LLM inference performance, organized by bottleneck type.

---

## 1. Quantization (Memory-Bound Decode)

### Model Weight Quantization

| Method | Bits | Quality | Speedup | Tool |
|--------|------|---------|---------|------|
| FP16 | 16 | Baseline | 1x | - |
| Q8_0 | 8 | ~Lossless | ~1.5x | llama.cpp |
| Q4_K_M | 4 | Good | ~3x | llama.cpp |
| Q3_K_M | 3 | Acceptable | ~4x | llama.cpp |
| GPTQ | 4 | Good | ~3x | AutoGPTQ |
| AWQ | 4 | Good | ~3x | AutoAWQ |
| FP8 | 8 | ~Lossless | ~1.5x | TRT-LLM |

**Recommendation**: Q4_K_M for llama.cpp, AWQ for vLLM/TRT-LLM. Best quality/speed tradeoff.

### KV Cache Quantization

```bash
# llama.cpp: INT8 KV cache
./llama-cli -m model.gguf --cache-type-k q8_0 --cache-type-v q8_0

# Saves ~50% KV cache memory, minimal quality impact
```

### Activation Quantization
- FP8 for GEMM operations (requires Hopper/Blackwell)
- INT8 for specific layers (layernorm, residual)

---

## 2. Batch Size Optimization

### Continuous Batching

Instead of waiting for all requests to finish, process requests dynamically:

```
Traditional:  [req1][req2][req3] → wait all → [req4][req5][req6]
Continuous:   [req1][req2][req3] → req1 done, req4 joins → [req2][req3][req4]
```

All modern frameworks support this. Enable it explicitly:
- llama.cpp: `--cont-batching`
- vLLM: enabled by default
- SGLang: enabled by default

### Chunked Prefill

Break long prefill into chunks to avoid blocking decode:

```
Without chunked prefill:
  [====prefill(2s)====][decode][decode][decode]
  
With chunked prefill:
  [prefill_chunk1][decode][prefill_chunk2][decode][decode]
```

- vLLM: `--enable-chunked-prefill`
- SGLang: `--chunked-prefill-size 4096`

---

## 3. Attention Optimization

### Flash Attention

Reduces memory access pattern from O(n²) to O(n) for attention computation.

- llama.cpp: `--flash-attn` (requires compilation with Flash Attention support)
- vLLM: enabled by default
- TRT-LLM: `--use_paged_context_fmha`

### PagedAttention

Allocates KV cache in fixed-size pages instead of contiguous memory:
- Eliminates memory fragmentation
- Enables KV cache sharing across requests
- vLLM's core innovation

### Multi-Query Attention (MQA) / Grouped-Query Attention (GQA)

Reduces KV cache size by sharing key/value heads across query heads:
- GQA: 8 KV heads instead of 32 (4x KV cache reduction)
- Most modern models (Llama, Qwen, Mistral) already use GQA

---

## 4. Kernel Fusion

### Fused Operations

| Fused Kernel | Replaces | Benefit |
|-------------|----------|---------|
| RMSNorm + Residual | 2 separate kernels | 1 launch instead of 2 |
| QKV Projection | 3 matmuls → 1 | Better memory locality |
| FFN Gate + Up | 2 matmuls → 1 | Shared weight loading |
| FlashAttention | Q×K^T, softmax, ×V | O(n) memory |

### CUDA Graphs

Capture a sequence of kernel launches and replay them:

```python
# PyTorch example
g = torch.cuda.CUDAGraph()
with torch.cuda.graph(g):
    output = model(input)

# Replay (much faster than individual launches)
g.replay()
```

- llama.cpp: not natively supported (manual implementation needed)
- vLLM: supports CUDA graphs for common shapes

---

## 5. Memory Optimization

### KV Cache Management

- **PagedAttention** (vLLM): dynamic page allocation
- **Prefix caching**: share KV cache for common system prompts
- **Sliding window**: limit attention to recent N tokens
- **KV cache eviction**: LRU or importance-based eviction

### Weight Sharing
- Tie embedding and output projection weights
- Share weights across layers (experimental)

### Offloading
- CPU offloading for large models: `--n-cpu-moe` (MoE layers on CPU)
- NVMe offloading for very large models

---

## 6. Parallelism

### Tensor Parallelism

Split model weights across GPUs:
- Each GPU holds 1/N of each layer's weights
- Requires NVLink for good performance
- vLLM: `--tensor-parallel-size N`
- TRT-LLM: `--world_size N`

### Pipeline Parallelism

Split model layers across GPUs:
- GPU 0: layers 0-15, GPU 1: layers 16-31
- Less communication than tensor parallelism
- Higher latency due to pipeline bubbles

### Data Parallelism

Replicate model across GPUs, split requests:
- SGLang: `--dp-size N`
- Best for throughput, not latency

---

## 7. Scheduling Optimization

### Priority Scheduling
- Prioritize decode (latency-sensitive) over prefill
- SGLang: `--schedule-policy lpm`

### Preemption
- Pause low-priority requests when memory is full
- vLLM supports preemption by recomputation or swap

### Load Balancing
- Distribute requests across multiple model instances
- Use a load balancer in front of multiple vLLM/TRT-LLM servers

---

## Decision Matrix

| Bottleneck | First Try | Second Try | Third Try |
|-----------|-----------|------------|-----------|
| Low throughput | Increase batch | Quantization | Tensor parallelism |
| High TTFT | FlashAttention | Chunked prefill | Reduce model size |
| High ITL | Quantization | KV cache quant | Increase batch |
| OOM | Reduce max_len | Quantization | PagedAttention |
| GPU idle | Continuous batching | Async scheduling | More concurrent requests |
| Many small kernels | CUDA graphs | Kernel fusion | Persistent kernels |
