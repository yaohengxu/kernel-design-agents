#!/usr/bin/env python3
"""
Parse llama-bench CSV output and produce a summary report.

Usage:
    # Generate CSV from llama-bench
    ./llama-bench -m model.gguf -p 512 -n 128 -r 3 -o csv > bench.csv

    # Parse
    python3 parse_llama_bench.py --csv bench.csv [--output summary.md]
"""

import argparse
import csv
import os
import sys


def parse_csv(filepath):
    """Parse llama-bench CSV output."""
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def format_summary(rows, run_name=""):
    """Format parsed rows as markdown summary."""
    lines = []
    lines.append(f"# llama-bench Summary: {run_name}\n")

    if not rows:
        lines.append("No data found.")
        return "\n".join(lines)

    # Detect column names (llama-bench format varies)
    # Common columns: model, size, backend, ngl, t/s prompt, t/s text gen, etc.
    lines.append("## Results\n")
    lines.append("| Model | Quant | Prompt (t/s) | Generate (t/s) | Prompt len | Gen len |")
    lines.append("|-------|-------|-------------|---------------|------------|---------|")

    for row in rows:
        model = row.get("model", row.get("Model", "unknown"))
        quant = row.get("quantization", row.get("Quantization", row.get("type_k", "-")))
        prompt_tps = row.get("t/s prompt", row.get("avg_ts_prompt", row.get("prompt_t/s", "N/A")))
        gen_tps = row.get("t/s text gen", row.get("avg_ts_gen", row.get("gen_t/s", "N/A")))
        prompt_len = row.get("prompt_n", row.get("n_prompt", row.get("pp", "N/A")))
        gen_len = row.get("text_gen_n", row.get("n_gen", row.get("tg", "N/A")))

        lines.append(f"| {model} | {quant} | {prompt_tps} | {gen_tps} | {prompt_len} | {gen_len} |")

    # Extract key numbers for quick reference
    lines.append("\n## Key Numbers\n")
    for row in rows:
        gen_tps = row.get("t/s text gen", row.get("avg_ts_gen", row.get("gen_t/s", "")))
        prompt_tps = row.get("t/s prompt", row.get("avg_ts_prompt", row.get("prompt_t/s", "")))
        if gen_tps:
            try:
                itl = 1000.0 / float(gen_tps)
                lines.append(f"- **Decode throughput**: {gen_tps} tokens/sec")
                lines.append(f"- **ITL (estimated)**: {itl:.1f} ms/token")
            except ValueError:
                pass
        if prompt_tps:
            lines.append(f"- **Prefill throughput**: {prompt_tps} tokens/sec")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse llama-bench CSV output")
    parser.add_argument("--csv", required=True, help="Path to llama-bench CSV file")
    parser.add_argument("--run-name", default="", help="Name for this benchmark run")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    rows = parse_csv(args.csv)
    report = format_summary(rows, args.run_name)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Summary written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
