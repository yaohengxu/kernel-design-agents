# Helpers

Reusable Python scripts for LLM inference benchmark analysis.

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `parse_llama_bench.py` | Parse llama-bench CSV output, extract throughput/latency | `python3 parse_llama_bench.py --csv bench.csv [--output summary.md]` |
| `parse_vllm_bench.py` | Parse vLLM benchmark_serving JSON output | `python3 parse_vllm_bench.py --json result.json [--output summary.md]` |
| `bottleneck_rank.py` | Rank kernels by time占比 from nsys/ncu reports | `python3 bottleneck_rank.py --nsys-stats kern.csv [--output bottlenecks.md]` |

## Typical Workflow

```bash
# 1. Run benchmark
./llama-bench -m model.gguf -p 512 -n 128 -r 3 -o csv > bench.csv

# 2. Parse benchmark results
python3 helpers/parse_llama_bench.py --csv bench.csv --output analysis/bench_summary.md

# 3. Profile with nsys
nsys profile --trace=cuda,nvtx,osrt --output=profile/run/report \
    ./llama-cli -m model.gguf -p 512 -n 128

# 4. Export nsys stats
nsys stats --report cuda_gpu_kern_sum profile/run/report.nsys-rep > profile/run/stats/kern.csv

# 5. Rank bottlenecks
python3 helpers/bottleneck_rank.py --nsys-stats profile/run/stats/kern.csv --output analysis/bottlenecks.md

# 6. For vLLM
python benchmark_serving.py --backend openai --model <model> --save-result
python3 helpers/parse_vllm_bench.py --json benchmark_result.json --output analysis/vllm_summary.md
```
