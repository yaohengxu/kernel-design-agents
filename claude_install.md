# Claude Code 安装指南

本文档说明如何将 kernel-design-agents 项目中的 agent 工作流和各个 skill 安装到 Claude Code。

---

## 项目定位

**kernel-design-agents** 不是 `.claude/agents/` 形式的 agent 配置文件，而是一套 **agent 驱动的 CUDA kernel 开发工作流**。它定义了"如何让 AI agent 高效地研究、实现、验证和迭代高性能 kernel"的方法论。

核心思想：把 kernel 开发拆成可重复的循环 — **定义合约 → 写计划 → 小步实现 → 每步验证 → 记录证据 → 推广或拒绝候选方案**。

### 与 Claude Code 的集成方式

| 组件 | 集成机制 | 说明 |
|------|---------|------|
| `CLAUDE.md` | **自动加载** — Claude Code 启动时读取当前仓库的 CLAUDE.md 作为系统指令 | 注入项目规则和工作流约束 |
| `prompts/basic-flow.md` | **手动输入** — 用户将模板内容贴给 Claude，填入任务合约 | 结构化 prompt，定义任务目标和流程步骤 |
| `skills/` | **需要安装** — 链接到 `~/.claude/skills/` 后自动发现 | 提供 domain knowledge（性能分析、硬件优化知识） |

三者配合的效果：Claude Code 在 kernel 开发任务中遵循"计划 → 实现 → 验证 → 记录证据"的工程化流程，而不是随意修改代码。

### 工作流概览

```
┌─────────────────────────────────────────────────────────┐
│  kernel-design-agents 仓库（参考材料，不直接改）          │
│                                                         │
│  CLAUDE.md              ← 自动注入的 agent 指令          │
│  prompts/basic-flow.md  ← 任务合约 + 工作流模板          │
│  skills/                ← domain skills（需安装）         │
│    ├─ ncu-report-skill    (Nsight Compute 分析)          │
│    ├─ nsys-profile-skill  (Nsight Systems 分析)          │
│    └─ KernelWiki          (Blackwell/Hopper 知识)        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  你的任务工作区（实际实现在这里）                          │
│                                                         │
│  docs/draft.md     ← agent 写的计划草案                  │
│  docs/plan.md      ← 可执行计划                          │
│  candidates.jsonl  ← 候选方案记录                         │
│  benchmark.csv     ← 性能数据                            │
│  profile/          ← profiling 证据                      │
└─────────────────────────────────────────────────────────┘
```

**使用方式**：在你的任务工作区中启动 Claude Code，把 `prompts/basic-flow.md` 的内容贴给 Claude 并填入任务合约。Claude 会自动加载 CLAUDE.md 的规则，按流程推进。需要性能分析或硬件知识时，skill 会被自动触发或手动调用。

---

## 项目组件一览

| 组件 | 类型 | 说明 |
|------|------|------|
| `CLAUDE.md` | 项目指令 | 仓库级 agent 指令，自动加载 |
| `prompts/basic-flow.md` | Prompt 模板 | 通用 kernel 开发流程模板 |
| `skills/ncu-report-skill` | Skill (子仓库) | Nsight Compute 内核级性能分析 |
| `skills/KernelWiki` | Skill (子仓库) | Blackwell/Hopper 内核优化知识库 |
| `skills/nsys-profile-skill` | Skill | Nsight Systems 应用级性能分析 |
| `skills/inference-bench-skill` | Skill | LLM 推理性能 benchmark 与瓶颈分析 |

---

## 1. 克隆项目

```bash
git clone --recurse-submodules git@github.com:yaohengxu/kernel-design-agents.git
cd kernel-design-agents
```

---

## 2. 安装 Skills

Claude Code 从两个位置发现 skills：

- `~/.claude/skills/<skill_name>/SKILL.md` — **用户级**，所有项目可用
- `<repo>/.claude/skills/<skill_name>/SKILL.md` — **项目级**，仅当前仓库可用

### 方式一：符号链接（推荐）

保持 skill 可版本控制，上游更新自动生效。

```bash
# 创建 skills 目录
mkdir -p ~/.claude/skills

# 逐个链接
ln -s "$(pwd)/skills/ncu-report-skill" ~/.claude/skills/ncu-report-skill
ln -s "$(pwd)/skills/KernelWiki" ~/.claude/skills/KernelWiki
ln -s "$(pwd)/skills/nsys-profile-skill" ~/.claude/skills/nsys-profile-skill
ln -s "$(pwd)/skills/inference-bench-skill" ~/.claude/skills/inference-bench-skill
```

验证：

```bash
ls -la ~/.claude/skills/
# 应看到三个指向本项目的符号链接
```

### 方式二：直接克隆到 ~/.claude/skills

```bash
mkdir -p ~/.claude/skills && cd ~/.claude/skills

# 子仓库 skill — 从上游克隆
git clone git@github.com:yaohengxu/ncu-report-skill.git
git clone git@github.com:yaohengxu/KernelWiki.git

# 本项目内置 skill — 需要从 kernel-design-agents 复制
cp -r /path/to/kernel-design-agents/skills/nsys-profile-skill .
cp -r /path/to/kernel-design-agents/skills/inference-bench-skill .
```

### 方式三：项目级安装（仅对特定仓库生效）

```bash
cd /path/to/your-workspace
mkdir -p .claude/skills

# 链接到 kernel-design-agents 中的 skills
ln -s /path/to/kernel-design-agents/skills/ncu-report-skill .claude/skills/ncu-report-skill
ln -s /path/to/kernel-design-agents/skills/KernelWiki .claude/skills/KernelWiki
ln -s /path/to/kernel-design-agents/skills/nsys-profile-skill .claude/skills/nsys-profile-skill
ln -s /path/to/kernel-design-agents/skills/inference-bench-skill .claude/skills/inference-bench-skill
```

---

## 3. 验证安装

启动 Claude Code 新会话，系统提示中应出现类似：

```
Available skills:
- ncu-report-skill: Profile CUDA kernels with Nsight Compute...
- KernelWiki: Use when the user asks about optimizing NVIDIA Blackwell/Hopper...
- nsys-profile-skill: Profile CUDA applications with Nsight Systems...
```

可手动调用：

```
/ncu-report-skill
/KernelWiki
/nsys-profile-skill
```

---

## 4. Skill 用途速查

| Skill | 触发场景 | 示例问题 |
|-------|---------|---------|
| **ncu-report-skill** | 单个 kernel 的性能分析 | "profile 这个 kernel"、"为什么这个 kernel 慢"、"ncu 报告怎么看" |
| **nsys-profile-skill** | 应用整体性能分析 | "GPU 利用率为什么低"、"CPU 和 GPU 有没有重叠"、"nsys 分析一下" |
| **inference-bench-skill** | LLM 推理性能优化 | "推理为什么慢"、"tokens/s 上不去"、"TTFT 太高"、"benchmark 一下" |
| **KernelWiki** | Blackwell/Hopper 内核优化知识 | "tcgen05 怎么用"、"FlashAttention-4 优化"、"Triton on Blackwell" |

### 典型工作流

```
通用 kernel 优化：
1. nsys-profile-skill  →  找到应用级瓶颈（哪个 kernel 占时最多、有无 gap）
2. ncu-report-skill    →  深入分析具体 kernel（memory-bound? compute-bound?）
3. KernelWiki          →  查找优化方案和最佳实践

LLM 推理优化：
1. inference-bench-skill →  benchmark → nsys → ncu → 优化 → 验证
2. ncu-report-skill      →  对瓶颈 kernel 做深入分析
3. KernelWiki            →  查找推理相关 kernel 优化知识
```

---

## 5. 使用 Agent 工作流

项目内置的 agent 工作流通过 prompt 模板驱动：

```bash
# 在你的实现工作区中启动 Claude Code
cd /path/to/your-implementation-workspace

# 将 prompts/ 下的模板内容作为 prompt 输入
```

### 通用 kernel 开发：`prompts/basic-flow.md`
1. 定义任务合约（目标、约束、验证命令）
2. 编写计划草案到 `docs/draft.md`
3. 小步迭代实现，每步验证
4. 记录候选方案、benchmark 结果、profiling 证据

### LLM 推理优化：`prompts/inference-optimize-flow.md`
1. 填入框架、模型、硬件、目标指标
2. 运行 baseline benchmark
3. nsys profile 找到 Top 瓶颈 kernel
4. ncu 深入分析瓶颈类型
5. 选择优化方案（量化、FlashAttention、batch 调优...）
6. 实现 → 重新 benchmark → 对比

---

## 6. 更新 Skills

### 符号链接方式（推荐）

```bash
cd /path/to/kernel-design-agents
git pull --recurse-submodules
# skills 自动更新，无需额外操作
```

### 克隆方式

```bash
cd ~/.claude/skills/ncu-report-skill && git pull
cd ~/.claude/skills/KernelWiki && git pull
cd ~/.claude/skills/nsys-profile-skill && git pull  # 需要从 kernel-design-agents 拉取
```

---

## 7. 故障排除

| 问题 | 解决 |
|------|------|
| Skill 未出现在系统提示中 | 检查 `~/.claude/skills/<name>/SKILL.md` 是否存在且有正确的 YAML frontmatter |
| 符号链接失效 | 确认目标路径存在：`ls -la ~/.claude/skills/` |
| ncu Python 模块找不到 | `export PYTHONPATH=$PYTHONPATH:/usr/local/cuda-*/nsight-compute-*/extras/python` |
| nsys 命令不存在 | 确认 CUDA Toolkit 已安装且 `nsys` 在 PATH 中 |
| 子仓库内容为空 | `git submodule update --init --recursive` |
