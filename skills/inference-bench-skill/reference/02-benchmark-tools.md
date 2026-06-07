# Benchmark Tools

## llama.cpp

### llama-bench (recommended for single-request latency)

```bash
# Basic benchmark
./llama-bench -m model.gguf -p 512 -n 128 -r 3

# With specific quantization
./llama-bench -m model-Q4_K_M.gguf -p 256,512,1024 -n 128 -r 3 -t 1

# CSV output for parsing
./llama-bench -m model.gguf -p 512 -n 128 -r 3 -o csv > bench.csv
```

Flags:
- `-p N`: prompt (prefill) token count
- `-n N`: generation (decode) token count
- `-r N`: repeat count for averaging
- `-t N`: thread count
- `-ngl N`: number of GPU layers
- `--batch-size N`: batch size for prompt processing
- `-o csv`: CSV output format

### llama-server (for serving throughput)

```bash
# Start server
./llama-server -m model.gguf -ngl 99 -c 4096 --host 0.0.0.0 --port 8080

# Benchmark with concurrent requests
curl -s http://localhost:8080/health
# Use external tools: wrk, hey, or custom scripts
```

---

## vLLM

### benchmark_serving.py

```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --quantization awq \
    --max-model-len 4096

# Benchmark
python benchmark_serving.py \
    --backend openai \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dataset-name sharegpt \
    --num-prompts 100 \
    --request-rate 10
```

Key flags:
- `--backend`: openai, vllm, tgi
- `--dataset-name`: sharegpt, random, sonnet
- `--num-prompts`: total requests to send
- `--request-rate`: requests per second (inf = all at once)

### benchmark_throughput.py (offline batch)

```bash
python benchmark_throughput.py \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dataset sharegpt \
    --num-prompts 1000 \
    --quantization awq
```

---

## TensorRT-LLM

```bash
# Throughput benchmark
trtllm-bench \
    --model Qwen/Qwen2.5-7B \
    --throughput \
    --max-batch-size 32 \
    --max-input-len 512 \
    --max-output-len 128

# Latency benchmark
trtllm-bench \
    --model Qwen/Qwen2.5-7B \
    --latency \
    --max-batch-size 1
```

---

## SGLang

```bash
# Start server
python -m sglang.launch_server \
    --model-path Qwen/Qwen2.5-7B-Instruct \
    --quantization awq

# Benchmark
python -m sglang.bench_serving \
    --backend openai \
    --model Qwen/Qwen2.5-7B-Instruct \
    --num-prompts 100
```

---

## Custom Benchmark Script

For frameworks without built-in benchmark tools:

```python
import time
import torch

def benchmark_generate(model, tokenizer, prompt, max_new_tokens=128, warmup=3, repeat=5):
    """Simple benchmark for any HuggingFace model."""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Warmup
    for _ in range(warmup):
        model.generate(**inputs, max_new_tokens=max_new_tokens)

    # Benchmark
    latencies = []
    for _ in range(repeat):
        torch.cuda.synchronize()
        start = time.perf_counter()
        output = model.generate(**inputs, max_new_tokens=max_new_tokens)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)

    output_tokens = output.shape[-1] - inputs["input_ids"].shape[-1]
    avg_latency = sum(latencies) / len(latencies)
    throughput = output_tokens / avg_latency

    print(f"Avg latency: {avg_latency*1000:.1f}ms")
    print(f"Output tokens: {output_tokens}")
    print(f"Throughput: {throughput:.1f} tokens/sec")
    print(f"ITL: {avg_latency/output_tokens*1000:.1f}ms")
```
