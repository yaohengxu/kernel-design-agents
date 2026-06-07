# Helpers

Reusable Python scripts for nsys report analysis.

## Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `parse_nsys_stats.py` | Parse `nsys stats` CSV output, extract key ratios | `python3 parse_nsys_stats.py --stats-dir <dir> [--output summary.md]` |
| `timeline_summary.py` | Generate ASCII timeline from nsys-rep (via SQLite export) | `python3 timeline_summary.py --sqlite report.sqlite [--output timeline.txt]` |
| `compare_runs.py` | Side-by-side comparison of two profiling runs | `python3 compare_runs.py --before before.md --after after.md [--output comparison.md]` |

## Typical workflow

```bash
# 1. Run nsys
nsys profile --trace=cuda,nvtx,osrt --cuda-memory-usage=true \
    --output=profile/run1/report ./my_app

# 2. Export stats
nsys stats --report cuda_api_sum profile/run1/report.nsys-rep > profile/run1/stats/cuda_api_sum.csv
nsys stats --report cuda_gpu_kern_sum profile/run1/report.nsys-rep > profile/run1/stats/cuda_gpu_kern_sum.csv
nsys stats --report cuda_gpu_mem_time_sum profile/run1/report.nsys-rep > profile/run1/stats/cuda_gpu_mem_time_sum.csv

# 3. Parse summary
python3 helpers/parse_nsys_stats.py --stats-dir profile/run1/stats/ --output profile/run1/analysis/summary.md

# 4. (Optional) Export to SQLite for timeline analysis
nsys export --type=sqlite --output=profile/run1/report.sqlite profile/run1/report.nsys-rep
python3 helpers/timeline_summary.py --sqlite profile/run1/report.sqlite --output profile/run1/analysis/timeline.txt

# 5. (Optional) Compare with another run
python3 helpers/compare_runs.py \
    --before profile/run1/analysis/summary.md \
    --after profile/run2/analysis/summary.md \
    --output profile/comparison.md
```
