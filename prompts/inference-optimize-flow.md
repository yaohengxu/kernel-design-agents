# LLM Inference Optimization Flow Prompt

You are working in a task implementation workspace. Your job is to optimize the LLM inference performance of the target framework/model/hardware combination described below.

## Task Contract

- Framework: `<fill in: llama.cpp | vLLM | TensorRT-LLM | SGLang | custom>`
- Model: `<fill in: model name and size, e.g., Qwen2.5-7B-Instruct>`
- Quantization: `<fill in: FP16 | Q4_K_M | Q8_0 | AWQ | GPTQ | FP8 | none>`
- Hardware: `<fill in: GPU model, e.g., RTX 5060 Ti 16GB>`
- Target metric: `<fill in: throughput (tokens/sec) | TTFT (ms) | ITL (ms) | P99 latency (ms)>`
- Baseline command: `<fill in: the exact benchmark command, e.g., ./llama-bench -m model.gguf -p 512 -n 128 -r 3>`
- Baseline result: `<fill in: current performance numbers if known>`
- Target: `<fill in: specific number or percentage improvement, e.g., 50 tokens/sec or 2x throughput>`
- Constraints: `<fill in: memory limit, precision requirement, max batch size, etc.>`

## Workflow

### Phase 1: Baseline Benchmark
1. Run the baseline benchmark command and record results.
2. Use the appropriate helper to parse results:
   - llama.cpp: `parse_llama_bench.py --csv bench.csv`
   - vLLM: `parse_vllm_bench.py --json result.json`
3. Record in `benchmark.csv`: framework, model, quant, gpu, tokens/sec, TTFT, ITL.

### Phase 2: Application-Level Profiling
4. Run nsys profile on the inference workload:
   ```bash
   nsys profile --trace=cuda,nvtx,osrt --cuda-memory-usage=true \
       --output=profile/<run_name>/report \
       <inference_command>
   ```
5. Export nsys stats and rank bottlenecks:
   ```bash
   nsys stats --report cuda_gpu_kern_sum profile/<run_name>/report.nsys-rep > stats/kern.csv
   python3 helpers/bottleneck_rank.py --nsys-stats stats/kern.csv --output bottlenecks.md
   ```
6. Identify the Top-3 kernels by total time.

### Phase 3: Kernel-Level Profiling (if needed)
7. For the top bottleneck kernel, run ncu:
   ```bash
   ncu --set full --section SourceCounters \
       --kernel-name "<kernel_name>" \
       --launch-skip 10 --launch-count 3 \
       -o profile/<run_name>/ncu_<kernel> \
       <inference_command>
   ```
8. Classify the kernel: memory-bound, compute-bound, latency-bound, or launch-bound.

### Phase 4: Optimize
9. Based on the bottleneck type, select optimization:
   - **Memory-bound decode**: Quantization (Q4_K_M, AWQ, GPTQ)
   - **Compute-bound prefill**: FlashAttention, chunked prefill
   - **Low occupancy**: Increase batch size
   - **Launch overhead**: CUDA graphs, kernel fusion
   - **KV cache**: PagedAttention, KV cache quantization
10. Implement the optimization.
11. Re-run baseline benchmark and compare.

### Phase 5: Verify and Report
12. Record before/after comparison in `benchmark.csv`.
13. Write optimization report in `docs/report.md`:
    - Baseline vs optimized numbers (table)
    - Profiling evidence (nsys/ncu metrics, kernel rankings)
    - What was changed and why
    - Remaining bottlenecks

## Plan Draft Requirements

The draft in `docs/draft.md` should include:

- Current baseline numbers and how they were measured.
- The main bottleneck(s) identified from profiling.
- Candidate optimization directions ranked by expected impact.
- The first concrete optimization to try.
- The exact commands to verify improvement.
- The evidence required to promote or reject each candidate.

Do not start optimization until the draft exists.

## Evidence Format

Record all benchmark results in a standard CSV:

```csv
framework,model,quant,gpu,batch_size,input_len,output_len,tokens_per_sec,ttft_ms,itl_ms,p50_ms,p99_ms,notes
```

Record candidate decisions in `candidates.jsonl`:

```json
{"name": "Q4_K_M quantization", "parent": null, "status": "promoted", "evidence": "ITL improved from 22ms to 8ms"}
```
