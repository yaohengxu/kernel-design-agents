# Profiling Report Template

Use this structure for the final report at `profile/<run_name>/REPORT.md`.

---

```markdown
# Profiling Report: <run_name>

## Summary

- **Application**: <name and version>
- **GPU**: <GPU model, e.g., RTX 5060 Ti / B200>
- **nsys version**: <version>
- **Trace duration**: <total wall-clock time>
- **Key finding**: <one-sentence summary of the main bottleneck>

## Metrics Overview

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| GPU Utilization | XX% | >80% | ✅ / ⚠️ / ❌ |
| Kernel Time Ratio | XX% | >70% | ✅ / ⚠️ / ❌ |
| Transfer Time Ratio | XX% | <10% | ✅ / ⚠️ / ❌ |
| Avg Launch Latency | XX μs | <10 μs | ✅ / ⚠️ / ❌ |
| Overlap Efficiency | XX% | >50% | ✅ / ⚠️ / ❌ |

## Timeline Analysis

### CPU-GPU Overlap

<describe the overlap pattern — sequential, partial, or good>

<include ASCII diagram if helpful>

### Memory Transfers

<describe whether transfers overlap with compute>

### Stream Utilization

<number of streams, whether they're actually concurrent>

## Bottleneck Analysis

### Bottleneck 1: <name>

- **Evidence**: <specific metric values and timeline observations>
- **Impact**: <estimated percentage of total time>
- **Root cause**: <why this happens>
- **Recommendation**: <concrete fix>

### Bottleneck 2: <name>

(same structure)

## Recommendations (ranked by impact)

1. **<recommendation>** — Expected improvement: XX%
   - <details on how to implement>
2. **<recommendation>** — Expected improvement: XX%
   - <details>

## Appendix: Raw Data

<nsys stats output, key screenshots, or SQLite query results>
```

---

## Writing guidelines

1. **Lead with the number.** Don't write "GPU utilization is low." Write "GPU utilization is 34%, well below the 80% target."

2. **Cite the evidence.** Every claim should reference a specific metric value or timeline observation. "The timeline shows kernel_A and kernel_B executing sequentially on stream 0, with a 12μs gap between them."

3. **Rank by impact.** The first recommendation should address the largest bottleneck. Don't list five equal-weight suggestions — quantify the expected improvement.

4. **Be specific about fixes.** Don't write "optimize memory transfers." Write "Move the cudaMalloc to initialization and use cudaMemcpyAsync on stream 1 to overlap with kernel execution on stream 0."

5. **Include the timeline.** Even in a text report, an ASCII diagram of the timeline is worth 1000 words. Show the before and expected after.
