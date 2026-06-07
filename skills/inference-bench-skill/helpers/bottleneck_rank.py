#!/usr/bin/env python3
"""
Rank bottleneck kernels from nsys stats or ncu reports.

Usage:
    # From nsys stats CSV
    python3 bottleneck_rank.py --nsys-stats profile/run/stats/kern.csv [--top 10]

    # From ncu report (requires ncu_report Python module)
    python3 bottleneck_rank.py --ncu-report profile/run/ncu_report.ncu-rep [--top 10]

    # Output
    python3 bottleneck_rank.py --nsys-stats stats.csv --output bottlenecks.md
"""

import argparse
import csv
import os
import sys


def parse_nsys_stats(filepath, top_n=10):
    """Parse nsys stats CSV and rank kernels by total time."""
    rows = []
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            if header is None:
                header = row
                continue
            rows.append(dict(zip(header, row)))

    # Parse total time
    kernels = []
    for row in rows:
        name = row.get("Name", "unknown")
        total_time_str = row.get("Total Time (ns)", "0")
        instances_str = row.get("Instances", "0")

        # Parse time string like "1.234 ms" or "567.890 us"
        total_ns = parse_time_ns(total_time_str)
        instances = int(instances_str.replace(",", ""))

        kernels.append({
            "name": name,
            "total_ns": total_ns,
            "instances": instances,
            "avg_ns": total_ns / instances if instances > 0 else 0,
        })

    # Sort by total time descending
    kernels.sort(key=lambda k: k["total_ns"], reverse=True)
    return kernels[:top_n]


def parse_time_ns(time_str):
    """Parse time string to nanoseconds."""
    if not time_str:
        return 0
    parts = time_str.strip().split()
    if len(parts) != 2:
        try:
            return float(time_str.replace(",", ""))
        except ValueError:
            return 0
    value = float(parts[0])
    unit = parts[1].lower()
    multipliers = {"ns": 1, "us": 1000, "ms": 1_000_000, "s": 1_000_000_000}
    return value * multipliers.get(unit, 1)


def parse_ncu_report(filepath, top_n=10):
    """Parse ncu report and rank kernels by GPU time."""
    try:
        from ncu_report import load_report
    except ImportError:
        print("Error: ncu_report module not found.", file=sys.stderr)
        print("Set PYTHONPATH to include ncu's extras/python directory.", file=sys.stderr)
        sys.exit(1)

    report = load_report(filepath)
    kernels = []

    for action in report.actions():
        name = action.name()
        gpu_time = action.gpu_time() if hasattr(action, "gpu_time") else 0
        kernels.append({
            "name": name,
            "total_ns": gpu_time,
            "instances": 1,
            "avg_ns": gpu_time,
        })

    kernels.sort(key=lambda k: k["total_ns"], reverse=True)
    return kernels[:top_n]


def classify_bottleneck(kernel_name):
    """Guess bottleneck type from kernel name."""
    name_lower = kernel_name.lower()
    if "attention" in name_lower or "flash" in name_lower:
        return "attention"
    elif "gemm" in name_lower or "matmul" in name_lower or "mm" in name_lower:
        return "compute"
    elif "norm" in name_lower or "layernorm" in name_lower or "rms" in name_lower:
        return "memory"
    elif "copy" in name_lower or "memcpy" in name_lower or "transfer" in name_lower:
        return "transfer"
    elif "reduce" in name_lower or "softmax" in name_lower:
        return "compute"
    else:
        return "other"


def format_report(kernels, title="Bottleneck Ranking"):
    """Format kernel ranking as markdown."""
    lines = []
    lines.append(f"# {title}\n")
    lines.append("| Rank | Kernel | Type | Total Time | Instances | Avg Time | % of Total |")
    lines.append("|------|--------|------|-----------|-----------|----------|------------|")

    total_time = sum(k["total_ns"] for k in kernels)

    for i, k in enumerate(kernels, 1):
        pct = k["total_ns"] / total_time * 100 if total_time > 0 else 0
        btype = classify_bottleneck(k["name"])
        lines.append(
            f"| {i} | `{k['name'][:50]}` | {btype} | "
            f"{k['total_ns']/1e6:.2f}ms | {k['instances']} | "
            f"{k['avg_ns']/1e6:.3f}ms | {pct:.1f}% |"
        )

    lines.append(f"\n**Total GPU time**: {total_time/1e6:.2f}ms")

    # Recommendations
    lines.append("\n## Recommendations\n")
    if kernels:
        top = kernels[0]
        btype = classify_bottleneck(top["name"])
        lines.append(f"**Focus on**: `{top['name'][:60]}` ({top['total_ns']/1e6:.2f}ms, {top['total_ns']/total_time*100:.1f}% of total)")
        lines.append("")
        if btype == "attention":
            lines.append("- Attention kernel dominates. Consider FlashAttention, KV cache optimization, or quantization.")
        elif btype == "compute":
            lines.append("- GEMM/MatMul dominates. Consider quantization, kernel fusion, or tensor cores.")
        elif btype == "memory":
            lines.append("- Memory operations dominate. Consider reducing data movement, kernel fusion.")
        elif btype == "transfer":
            lines.append("- Memory transfers dominate. Consider overlapping transfers with compute, use pinned memory.")
        else:
            lines.append("- Profile this kernel with ncu for detailed analysis.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Rank bottleneck kernels")
    parser.add_argument("--nsys-stats", default=None, help="Path to nsys stats CSV")
    parser.add_argument("--ncu-report", default=None, help="Path to ncu report file")
    parser.add_argument("--top", type=int, default=10, help="Number of top kernels to show")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    if args.nsys_stats:
        kernels = parse_nsys_stats(args.nsys_stats, args.top)
        title = "Bottleneck Ranking (from nsys)"
    elif args.ncu_report:
        kernels = parse_ncu_report(args.ncu_report, args.top)
        title = "Bottleneck Ranking (from ncu)"
    else:
        print("Error: provide --nsys-stats or --ncu-report", file=sys.stderr)
        sys.exit(1)

    report = format_report(kernels, title)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
