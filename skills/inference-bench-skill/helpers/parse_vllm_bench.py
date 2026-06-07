#!/usr/bin/env python3
"""
Parse vLLM benchmark_serving JSON output and produce a summary.

Usage:
    # Run vLLM benchmark (outputs JSON)
    python benchmark_serving.py --backend openai --model <model> \
        --dataset-name sharegpt --num-prompts 100 --save-result

    # Parse
    python3 parse_vllm_bench.py --json benchmark_result.json [--output summary.md]
"""

import argparse
import json
import os
import sys


def parse_json(filepath):
    """Parse vLLM benchmark JSON output."""
    with open(filepath, "r") as f:
        return json.load(f)


def format_summary(data, run_name=""):
    """Format parsed data as markdown summary."""
    lines = []
    lines.append(f"# vLLM Benchmark Summary: {run_name}\n")

    if not data:
        lines.append("No data found.")
        return "\n".join(lines)

    lines.append("## Key Metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

    # Extract standard vLLM benchmark fields
    metrics = {
        "Successful requests": data.get("completed", "N/A"),
        "Benchmark duration (s)": f"{data.get('benchmark_duration', 0):.2f}",
        "Total input tokens": data.get("total_input_tokens", "N/A"),
        "Total generated tokens": data.get("total_generated_tokens", "N/A"),
        "Request throughput (req/s)": f"{data.get('request_throughput', 0):.4f}",
        "Output token throughput (tok/s)": f"{data.get('output_throughput', 0):.2f}",
        "Total token throughput (tok/s)": f"{data.get('total_token_throughput', 0):.2f}",
    }

    # Latency metrics
    if "mean_latency_ms" in data:
        metrics["Mean latency (ms)"] = f"{data['mean_latency_ms']:.2f}"
    if "median_latency_ms" in data:
        metrics["P50 latency (ms)"] = f"{data['median_latency_ms']:.2f}"
    if "p99_latency_ms" in data:
        metrics["P99 latency (ms)"] = f"{data['p99_latency_ms']:.2f}"

    # TTFT
    if "mean_ttft_ms" in data:
        metrics["Mean TTFT (ms)"] = f"{data['mean_ttft_ms']:.2f}"
    if "median_ttft_ms" in data:
        metrics["P50 TTFT (ms)"] = f"{data['median_ttft_ms']:.2f}"
    if "p99_ttft_ms" in data:
        metrics["P99 TTFT (ms)"] = f"{data['p99_ttft_ms']:.2f}"

    # ITL
    if "mean_itl_ms" in data:
        metrics["Mean ITL (ms)"] = f"{data['mean_itl_ms']:.2f}"
    if "median_itl_ms" in data:
        metrics["P50 ITL (ms)"] = f"{data['median_itl_ms']:.2f}"
    if "p99_itl_ms" in data:
        metrics["P99 ITL (ms)"] = f"{data['p99_itl_ms']:.2f}"

    for key, value in metrics.items():
        lines.append(f"| {key} | {value} |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse vLLM benchmark JSON output")
    parser.add_argument("--json", required=True, help="Path to vLLM benchmark JSON file")
    parser.add_argument("--run-name", default="", help="Name for this benchmark run")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    data = parse_json(args.json)
    report = format_summary(data, args.run_name)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Summary written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
