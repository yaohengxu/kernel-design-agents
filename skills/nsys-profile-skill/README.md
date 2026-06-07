# nsys-profile-skill

A Claude Code skill for profiling CUDA applications with Nsight Systems (nsys). Covers the full workflow: run nsys with the right flags, analyze the execution timeline, identify CPU-GPU overlap issues, quantify bottlenecks, and write an evidence-backed optimization report.

The skill is self-contained: reference docs, reusable helper scripts, and common pattern checklists all ship in this repo.

---

## What's in this repo

```
.
├── SKILL.md                          ← skill entry point (with YAML frontmatter)
├── README.md                         ← this file
├── helpers/                          ← reusable scripts
│   ├── parse_nsys_stats.py           ← parse nsys stats CSV, extract key ratios
│   ├── timeline_summary.py           ← ASCII timeline summary from nsys-rep
│   ├── compare_runs.py               ← side-by-side comparison of two runs
│   └── README.md
└── reference/                        ← detailed reference docs
    ├── 01-collection.md              ← nsys command recipes
    ├── 02-analysis.md                ← how to read the timeline, use nsys-ui/CLI
    ├── 03-metrics.md                 ← key metrics and what they mean
    ├── 04-report-template.md         ← final report structure
    ├── 05-common-patterns.md         ← performance anti-patterns and fixes
    └── 06-nsys-vs-ncu.md             ← when to use nsys vs ncu
```

---

## Installation

Claude Code discovers skills in two locations:

- `~/.claude/skills/<skill_name>/SKILL.md` — **user-level**, available in every project
- `<repo>/.claude/skills/<skill_name>/SKILL.md` — **project-level**, scoped to one repo

### Option 1 — Symlink from a clone (recommended)

```bash
# Clone somewhere stable
git clone git@github.com:yaohengxu/nsys-profile-skill.git ~/workspace/nsys-profile-skill

# User-level install
mkdir -p ~/.claude/skills
ln -s ~/workspace/nsys-profile-skill ~/.claude/skills/nsys-profile-skill

# Or project-level install
cd /path/to/other-repo
mkdir -p .claude/skills
ln -s ~/workspace/nsys-profile-skill .claude/skills/nsys-profile-skill
```

### Option 2 — Copy into place

```bash
git clone git@github.com:yaohengxu/nsys-profile-skill.git /tmp/nsys
mkdir -p ~/.claude/skills
cp -r /tmp/nsys ~/.claude/skills/nsys-profile-skill
```

### Option 3 — Git submodule

```bash
cd /path/to/other-repo
git submodule add git@github.com:yaohengxu/nsys-profile-skill.git .claude/skills/nsys-profile-skill
git commit -m "Add nsys-profile-skill as a submodule"
```

---

## How Claude uses this skill

Once installed, Claude Code will:

1. Advertise the skill's name + description in the system reminder of new conversations.
2. Let the user invoke it manually via `/nsys-profile-skill` or let the model invoke it when the conversation matches the `description` triggers.

When invoked, Claude reads `SKILL.md`, follows its workflow, and uses the helper scripts in `helpers/` as needed.

---

## When to use nsys vs ncu

| Tool | What it answers | Example questions |
|------|----------------|-------------------|
| **nsys** | **When** and **how** things happen — timeline, overlap, gaps | "为什么 GPU 利用率只有 30%?" "CPU 和 GPU 有没有重叠?" "launch overhead 多大?" |
| **ncu** | **Why** a specific kernel is slow — stalls, memory, occupancy | "这个 kernel 为什么慢?" "是 compute-bound 还是 memory-bound?" "怎么优化?" |

**Use nsys first** to find *where* the bottleneck is (application level), then **use ncu** to drill into *why* a specific kernel underperforms.

---

## Requirements

- NVIDIA Nsight Systems CLI (`nsys`) — tested with 2024.x+ and 2026.x
- An NVIDIA GPU with driver support for the features you're tracing
- For GPU metrics: `--gpu-metrics-device` requires appropriate driver and permissions
- Python 3.8+ for helper scripts (optional)

---

## License

MIT
