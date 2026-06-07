# inference-bench-skill

A Claude Code skill for profiling and optimizing LLM inference performance on NVIDIA GPUs. Covers the full workflow: baseline benchmark, application-level profiling (nsys), kernel-level profiling (ncu), bottleneck diagnosis, optimization implementation, and verification.

---

## What's in this repo

```
.
├── SKILL.md                              ← skill entry point (with YAML frontmatter)
├── README.md                             ← this file
├── reference/
│   ├── 01-metrics.md                     ← LLM inference metrics definitions
│   ├── 02-benchmark-tools.md             ← benchmark tools for each framework
│   ├── 03-profiling-workflow.md          ← nsys→ncu two-stage profiling
│   ├── 04-bottleneck-playbook.md         ← bottleneck → cause → fix
│   ├── 05-framework-guide.md             ← framework-specific tips
│   └── 06-optimization-catalog.md        ← optimization techniques catalog
└── helpers/
    ├── parse_llama_bench.py              ← parse llama-bench CSV output
    ├── parse_vllm_bench.py               ← parse vLLM benchmark_serving JSON
    ├── bottleneck_rank.py                ← rank kernels by time占比
    └── README.md
```

---

## Supported Frameworks

| Framework | Benchmark Tool | Profile Method |
|-----------|---------------|----------------|
| **llama.cpp** | `llama-bench` | nsys + ncu on llama-cli |
| **vLLM** | `benchmark_serving.py` | nsys + ncu on vllm process |
| **TensorRT-LLM** | `trtllm-bench` | nsys + ncu on trtllm process |
| **SGLang** | `sglang bench_serving` | nsys + ncu on sglang process |

---

## Installation

```bash
# Symlink (recommended)
mkdir -p ~/.claude/skills
ln -s /path/to/kernel-design-agents/skills/inference-bench-skill ~/.claude/skills/inference-bench-skill

# Or copy
cp -r /path/to/kernel-design-agents/skills/inference-bench-skill ~/.claude/skills/
```

---

## Typical Workflow

```
1. Baseline benchmark     →  tokens/sec, TTFT, ITL
2. nsys profile           →  Top-3 kernels by time, CPU-GPU overlap
3. ncu profile (Top-N)    →  memory-bound? compute-bound? latency-bound?
4. Optimize               →  quantization, batch, kernel fusion, ...
5. Re-benchmark           →  compare with baseline
6. Report                 →  evidence-backed optimization report
```

---

## Requirements

- NVIDIA GPU with CUDA support
- llama.cpp compiled with CUDA (`-DGGML_CUDA=ON`), or vLLM/TRT-LLM installed
- Nsight Systems (`nsys`) and Nsight Compute (`ncu`) — for profiling phases
- Python 3.8+ for helper scripts

---

## License

MIT
