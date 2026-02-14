# CodeRabbit Config Generator

![Skill to turn your project's recent PR history and commit messages into CodeRabbit checks that match the issues you actually see in practice](alchemiststudios-coderabbit-2.webp)

A [Claude Code skill](https://code.claude.com/docs/en/skills) that analyzes your project's PR history and commit messages to generate a `.coderabbit.yaml` tailored to the issues you actually see in practice.

## Install

Clone this repo into your Claude Code skills directory:

```bash
git clone https://github.com/alchemiststudiosDOTai/coderabbit-config-generator.git \
  ~/.claude/skills/coderabbit-config-generator
```

The skill is now available in all your projects.

## Usage

Ask Claude to run the skill on your current repository:

> Run the CodeRabbit config generator skill for this repo using the last 90 days of PRs and commits.

Or invoke it directly:

```
/coderabbit-config-generator
```

The skill will:

1. Pull recent PRs and commits via the GitHub CLI
2. Scan for recurring patterns (common issues, edge cases, anti-patterns)
3. Generate a `.coderabbit.yaml` with custom review checks matched to your project

## Prerequisites

- GitHub CLI (`gh`) authenticated
- Python 3
- A local git clone of the repository you want to analyze

## Running the scripts directly

```bash
~/.claude/skills/coderabbit-config-generator/scripts/run_analysis.sh \
  --repo-path /path/to/repo --repo owner/name
```

## Validating a config

Requires PyYAML (`pip install pyyaml`):

```bash
python3 ~/.claude/skills/coderabbit-config-generator/scripts/validate_coderabbit_yaml.py \
  --config .coderabbit.yaml
```

## Tuning patterns

Edit `scripts/patterns.json` to add or refine keyword and regex matches used during analysis.

## Skill structure

```
coderabbit-config-generator/
├── SKILL.md                              # Skill entrypoint (instructions for Claude)
├── README.md                             # This file
├── scripts/
│   ├── run_analysis.sh                   # Main analysis runner
│   ├── collect_prs.sh                    # PR data collection
│   ├── collect_commits.sh                # Commit log collection
│   ├── analyze_patterns.py               # Pattern detection
│   ├── validate_coderabbit_yaml.py       # Config validator
│   └── patterns.json                     # Tunable pattern definitions
└── alchemiststudios-coderabbit-2.webp    # Banner image
```
