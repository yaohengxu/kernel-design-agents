#!/usr/bin/env python3
"""
Generate ASCII timeline summary from nsys-rep (via SQLite export).

Usage:
    # First export to SQLite:
    nsys export --type=sqlite --output=report.sqlite report.nsys-rep

    # Then run:
    python3 timeline_summary.py --sqlite report.sqlite [--output timeline.txt] [--max-rows 20]
"""

import argparse
import os
import sqlite3
import sys


def get_connection(sqlite_path):
    """Open SQLite connection."""
    if not os.path.exists(sqlite_path):
        print(f"Error: {sqlite_path} not found", file=sys.stderr)
        sys.exit(1)
    return sqlite3.connect(sqlite_path)


def get_kernels(conn, limit=1000):
    """Fetch kernel executions from the SQLite DB."""
    # The exact schema varies by nsys version; try common table names
    queries = [
        "SELECT start, end, shortName FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start LIMIT ?",
        "SELECT start, end, name FROM CUPTI_ACTIVITY_KIND_KERNEL ORDER BY start LIMIT ?",
    ]
    for q in queries:
        try:
            rows = conn.execute(q, (limit,)).fetchall()
            return rows
        except sqlite3.OperationalError:
            continue
    print("Error: Could not find kernel table in SQLite. Check nsys version.", file=sys.stderr)
    return []


def get_transfers(conn, limit=1000):
    """Fetch memory transfer events."""
    queries = [
        "SELECT start, end, bytes, copyKind FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start LIMIT ?",
        "SELECT start, end, bytes, type FROM CUPTI_ACTIVITY_KIND_MEMCPY ORDER BY start LIMIT ?",
    ]
    for q in queries:
        try:
            rows = conn.execute(q, (limit,)).fetchall()
            return rows
        except sqlite3.OperationalError:
            continue
    return []


def ns_to_str(ns):
    """Convert nanoseconds to human-readable string."""
    if ns < 1000:
        return f"{ns:.0f}ns"
    elif ns < 1_000_000:
        return f"{ns / 1000:.1f}μs"
    elif ns < 1_000_000_000:
        return f"{ns / 1_000_000:.1f}ms"
    else:
        return f"{ns / 1_000_000_000:.2f}s"


def render_ascii_timeline(events, total_width=80, title="Timeline"):
    """Render an ASCII timeline."""
    if not events:
        return f"  {title}: (no events)\n"

    min_t = min(e[0] for e in events)
    max_t = max(e[1] for e in events)
    duration = max_t - min_t

    if duration == 0:
        return f"  {title}: single instant at {ns_to_str(min_t)}\n"

    lines = []
    lines.append(f"  {title} ({ns_to_str(duration)} total)")
    lines.append(f"  {'|' + '-' * (total_width - 2) + '|'}")

    for i, (start, end, *rest) in enumerate(events[:50]):  # cap at 50 rows
        name = rest[0] if rest else f"event_{i}"
        # Truncate name
        name = str(name)[:20]
        s_pos = int((start - min_t) / duration * (total_width - 2))
        e_pos = int((end - min_t) / duration * (total_width - 2))
        e_pos = max(e_pos, s_pos + 1)  # at least 1 char

        row = [" "] * total_width
        row[0] = "|"
        row[-1] = "|"
        for j in range(s_pos + 1, min(e_pos + 1, total_width - 1)):
            row[j] = "█"

        lines.append(f"  {''.join(row)}  {name}")

    if len(events) > 50:
        lines.append(f"  ... and {len(events) - 50} more events")

    return "\n".join(lines)


def analyze_gaps(events):
    """Find gaps between consecutive events."""
    if len(events) < 2:
        return []

    sorted_events = sorted(events, key=lambda e: e[0])
    gaps = []
    for i in range(1, len(sorted_events)):
        gap_start = sorted_events[i - 1][1]
        gap_end = sorted_events[i][0]
        gap_duration = gap_end - gap_start
        if gap_duration > 0:
            gaps.append((gap_start, gap_end, gap_duration))

    gaps.sort(key=lambda g: g[2], reverse=True)
    return gaps


def main():
    parser = argparse.ArgumentParser(description="Generate ASCII timeline from nsys SQLite")
    parser.add_argument("--sqlite", required=True, help="Path to nsys-exported SQLite file")
    parser.add_argument("--output", default=None, help="Output file (default: stdout)")
    parser.add_argument("--max-rows", type=int, default=20, help="Max events per timeline")
    parser.add_argument("--width", type=int, default=80, help="Timeline width in characters")
    args = parser.parse_args()

    conn = get_connection(args.sqlite)
    lines = []

    # Kernel timeline
    kernels = get_kernels(conn, limit=args.max_rows)
    lines.append(render_ascii_timeline(kernels, args.width, "GPU Kernels"))

    # Transfer timeline
    transfers = get_transfers(conn, limit=args.max_rows)
    if transfers:
        lines.append("")
        lines.append(render_ascii_timeline(transfers, args.width, "Memory Transfers"))

    # Gap analysis
    if kernels:
        lines.append("\n  Largest gaps between kernels:")
        gaps = analyze_gaps(kernels)
        for start, end, dur in gaps[:5]:
            lines.append(f"    {ns_to_str(dur)} gap at {ns_to_str(start)} - {ns_to_str(end)}")

    conn.close()

    report = "\n".join(lines)
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Timeline written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
