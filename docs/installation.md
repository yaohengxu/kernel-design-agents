# Installation Guide

This repository is a Claude Code Agent workflow template. Installation means configuring skills, agent instructions, and prompt templates — not installing a package.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- Git with submodule support
- Python 3.10+ (for KernelWiki query scripts)

## Quick Start

```bash
# 1. Clone with submodules
git clone --recurse-submodules git@github.com:yaohengxu/kernel-design-agents.git
cd kernel-design-agents

# 2. Install skills (choose one method below)
# 3. Start using
```

## Skills Installation

Claude Code discovers skills by looking for `SKILL.md` inside directories under `~/.claude/skills/` (user-level) or `<repo>/.claude/skills/` (project-level).

### Method A — Symlink (Recommended)

Links the cloned skill directories into Claude Code's discovery path. Changes to skill code take effect immediately.

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/skills/ncu-report-skill" ~/.claude/skills/ncu-report-skill
ln -s "$(pwd)/skills/KernelWiki" ~/.claude/skills/KernelWiki
ln -s "$(pwd)/skills/nsys-profile-skill" ~/.claude/skills/nsys-profile-skill
ln -s "$(pwd)/skills/inference-bench-skill" ~/.claude/skills/inference-bench-skill
```

### Method B — Project-level Symlink

Scoped to this repository only. Useful when different projects need different skill versions.

```bash
mkdir -p .claude/skills
ln -s "$(pwd)/skills/ncu-report-skill" .claude/skills/ncu-report-skill
ln -s "$(pwd)/skills/KernelWiki" .claude/skills/KernelWiki
ln -s "$(pwd)/skills/nsys-profile-skill" .claude/skills/nsys-profile-skill
ln -s "$(pwd)/skills/inference-bench-skill" .claude/skills/inference-bench-skill
```

### Method C — Standalone Clone

Clone skills directly into `~/.claude/skills/`. No symlink needed, but updates require manual pulls.

```bash
mkdir -p ~/.claude/skills
git clone git@github.com:yaohengxu/ncu-report-skill.git ~/.claude/skills/ncu-report-skill
git clone git@github.com:yaohengxu/KernelWiki.git ~/.claude/skills/KernelWiki
# nsys-profile-skill and inference-bench-skill are in the kernel-design-agents repo
cp -r skills/nsys-profile-skill ~/.claude/skills/
cp -r skills/inference-bench-skill ~/.claude/skills/
```

## KernelWiki Dependencies

```bash
pip install -r skills/KernelWiki/requirements.txt
```

Verify the installation:

```bash
cd skills/KernelWiki
python3 scripts/query.py --tag nvfp4 --type kernel --compact
python3 scripts/get_page.py kernel-flash-attention-4 --frontmatter-only
```

## How It Works

### CLAUDE.md — Agent Instructions

`CLAUDE.md` at the repository root is automatically read at the start of every Claude Code session in this directory. It defines:

- Repository rules and constraints
- The expected agent workflow (plan → implement → validate → record)
- Optional skills to use

Priority hierarchy:

| Location | Scope | Committed to Git? |
|---|---|---|
| `~/.claude/CLAUDE.md` | User-level, all projects | No |
| `<repo>/CLAUDE.md` | Project-level, shared | Yes |
| `<repo>/CLAUDE.local.md` | Project-level, personal | No |

### SKILL.md — Skill Entry Point

Each skill has a `SKILL.md` with YAML frontmatter:

```yaml
---
name: ncu-report-skill
description: Profile CUDA kernels with Nsight Compute on B200...
argument-hint: "[question] | [--tag foo --type kernel]"
allowed-tools: "Bash Read Grep Glob"
---
```

- `name` — the slash command (e.g., `/ncu-report-skill`)
- `description` — when to auto-invoke the skill
- `allowed-tools` — tools the skill can use

### Prompt Templates

Task-specific prompts in `prompts/` are not auto-loaded. Copy them into a session after filling in the task contract fields.

## Usage

```bash
# Create a task workspace (separate from this repo)
mkdir ~/my-task && cd ~/my-task
git init

# Start Claude Code
claude

# In the session, paste the filled-in prompt from prompts/basic-flow.md
# Or for LLM inference optimization, use prompts/inference-optimize-flow.md
# Or invoke skills directly:
#   /ncu-report-skill        — CUDA kernel profiling
#   /nsys-profile-skill      — application-level profiling
#   /inference-bench-skill   — LLM inference optimization
#   /KernelWiki              — Blackwell/Hopper optimization knowledge base
```

## Repository Structure

```
kernel-design-agents/
├── CLAUDE.md                  ← agent instructions (auto-read)
├── docs/
│   ├── agent-flow.md          ← workflow documentation
│   └── installation.md        ← this file
├── prompts/
│   ├── basic-flow.md          ← starter prompt template
│   └── README.md              ← how to use templates
└── skills/
    ├── ncu-report-skill/      ← CUDA profiling skill (submodule)
    │   ├── SKILL.md
    │   ├── helpers/
    │   └── reference/
    ├── KernelWiki/            ← kernel optimization wiki (submodule)
    │   ├── SKILL.md
    │   ├── scripts/
    │   └── wiki/
    ├── nsys-profile-skill/    ← application-level profiling skill
    │   ├── SKILL.md
    │   ├── helpers/
    │   └── reference/
    └── inference-bench-skill/ ← LLM inference optimization skill
        ├── SKILL.md
        ├── helpers/
        └── reference/
```

## Troubleshooting

**Skills not appearing in Claude Code:**
- Verify `SKILL.md` exists in the skill directory
- Check symlink target is valid: `ls -la ~/.claude/skills/`
- Restart Claude Code after adding new skills

**KernelWiki scripts fail:**
- Ensure `requirements.txt` is installed
- Try setting `BLACKWELL_WIKI_ROOT` explicitly: `export BLACKWELL_WIKI_ROOT=/path/to/KernelWiki`
