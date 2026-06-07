#!/usr/bin/env python3
"""
Compare two nsys profiling runs side by side.

Usage:
    python3 compare_runs.py \
        --before profile/run_before/analysis/summary.md \
        --after profile/run_after/analysis/summary.md \
        [--output comparison.md]
"""

import argparse
import re
import sys


def parse_metrics(filepath):
    """Parse key metrics from a summary markdown file."""
    metrics = {}
    with open(filepath, "r") as f:
        content = f.read()

    # Extract table rows
    for match in re.finditer(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|", content):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key in ("Metric", "---", "--------"):
            continue
        metrics[key] = value

    return metrics


def parse_value(value_str):
    """Try to extract a numeric value from a string like '1.234 ms'."""
    match = re.match(r"([\d.]+)\s*(μs|ms|s|GB|MB|KB|B|%)", value_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2)
        # Normalize to common units
        multipliers = {
            "μs": 1, "ms": 1000, "s": 1_000_000,
            "B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3,
            "%": 1,
        }
        return num * multipliers.get(unit, 1)
    try:
        return float(value_str.replace(",", ""))
    except ValueError:
        return None


def compare(before_metrics, after_metrics):
    """Generate comparison report."""
    lines = []
    lines.append("# Profiling Comparison\n")
    lines.append("| Metric | Before | After | Change |")
    lines.append("|--------|--------|-------|--------|")

    all_keys = sorted(set(list(before_metrics.keys()) + list(after_metrics.keys())))

    for key in all_keys:
        before = before_metrics.get(key, "N/A")
        after = after_metrics.get(key, "N/A")

        # Try to compute change
        change = ""
        before_val = parse_value(before)
        after_val = parse_value(after)

        if before_val is not None and after_val is not None and before_val != 0:
            pct = (after_val - before_val) / before_val * 100
            if "%" in before:
                change = f"{after_val - before_val:+.1f}pp"
            elif pct > 0:
                change = f"+{pct:.1f}% ⚠️"
            else:
                change = f"{pct:.1f}% ✅"

        lines.append(f"| {key} | {before} | {after} | {change} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare two nsys profiling runs")
    parser.add_argument("--before", required=True, help="Before run summary markdown")
    parser.add_argument("--after", required=True, help="After run summary markdown")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    before_metrics = parse_metrics(args.before)
    after_metrics = parse_metrics(args.after)
    report = compare(before_metrics, after_metrics)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Comparison written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
