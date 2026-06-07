# Framework-Specific Guide

## llama.cpp

### Architecture
- Single-process, CPU+GPU hybrid inference
- GGUF format for quantized models
- Metal/CUDA/Vulkan backends

### Key Commands

```bash
# Build with CUDA
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89
cmake --build build -j

# Benchmark
./build/bin/llama-bench -m model.gguf -p 512 -n 128 -r 3 -o csv

# Profile with nsys
nsys profile --trace=cuda,nvtx,osrt --output=profile/run \
    ./build/bin/llama-cli -m model.gguf -p 512 -n 128

# Server mode
./build/bin/llama-server -m model.gguf -ngl 99 -c 4096
```

### Optimization Knobs
- `-ngl N`: number of GPU layers (offload more to GPU)
- `--batch-size N`: prompt processing batch size
- `-t N`: CPU thread count
- `--flash-attn`: enable Flash Attention (if compiled in)
- `--cont-batching`: enable continuous batching in server mode
- `--cache-type-k q8_0`: KV cache quantization

### Common Issues
- **Low GPU utilization**: not enough layers offloaded (`-ngl 99`)
- **Slow prefill**: increase `--batch-size` or enable `--flash-attn`
- **High memory usage**: reduce context length (`-c`) or use KV cache quantization

---

## vLLM

### Architecture
- Python-based serving framework
- PagedAttention for efficient KV cache management
- Continuous batching by default

### Key Commands

```bash
# Install
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --quantization awq \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9

# Benchmark serving
python -m vllm.entrypoints.openai.api_server --model <model> &
python benchmark_serving.py --backend openai --model <model> \
    --dataset-name sharegpt --num-prompts 100

# Benchmark throughput (offline)
python benchmark_throughput.py --model <model> --num-prompts 1000
```

### Optimization Knobs
- `--quantization awq/gptq`: model quantization
- `--max-model-len N`: max sequence length (affects KV cache size)
- `--gpu-memory-utilization 0.9`: GPU memory fraction for KV cache
- `--tensor-parallel-size N`: multi-GPU tensor parallelism
- `--enable-chunked-prefill`: chunked prefill for mixed workloads
- `--max-num-seqs N`: max concurrent sequences
- `--max-num-batched-tokens N`: max tokens per batch

### Common Issues
- **Low throughput**: increase `--max-num-seqs` or `--gpu-memory-utilization`
- **High TTFT**: enable `--enable-chunked-prefill`
- **OOM**: reduce `--max-model-len` or use quantization

---

## TensorRT-LLM

### Architecture
- Compiled/optimized inference engine
- Supports FP8, INT8, INT4 quantization
- Multi-GPU with tensor/pipeline parallelism

### Key Commands

```bash
# Build engine
trtllm-build \
    --checkpoint_dir ./ckpt \
    --output_dir ./engine \
    --gemm_plugin float16 \
    --max_batch_size 32 \
    --max_input_len 512 \
    --max_seq_len 1024

# Benchmark throughput
trtllm-bench --model ./engine --throughput \
    --max-batch-size 32 --max-input-len 512

# Benchmark latency
trtllm-bench --model ./engine --latency --max-batch-size 1
```

### Optimization Knobs
- `--gemm_plugin float16/int8`: GEMM precision
- `--max_batch_size N`: batch size limit
- `--use_paged_context_fmha`: paged attention
- `--reduce_fusion`: fuse reduce operations
- `--use_fp8_context_fmha`: FP8 attention

---

## SGLang

### Architecture
- RadixAttention for KV cache reuse
- Compressed finite state machine for structured output
- Fast constrained decoding

### Key Commands

```bash
# Start server
python -m sglang.launch_server \
    --model-path Qwen/Qwen2.5-7B-Instruct \
    --quantization awq \
    --mem-fraction-static 0.85

# Benchmark
python -m sglang.bench_serving \
    --backend openai \
    --model Qwen/Qwen2.5-7B-Instruct \
    --num-prompts 100
```

### Optimization Knobs
- `--quantization awq/gptq`: quantization
- `--mem-fraction-static 0.85`: memory allocation ratio
- `--schedule-policy lpm`: scheduling policy (longest prefix match)
- `--chunked-prefill-size N`: chunked prefill size
- `--dp-size N`: data parallelism
