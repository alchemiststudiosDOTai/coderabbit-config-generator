# CodeRabbit Config Generator

![Skill to turn your project's recent PR history and commit messages into CodeRabbit checks that match the issues you actually see in practice](alchemiststudios-coderabbit-2.webp)

A Claude Code skill that turns your project's recent PR history and commit messages into [CodeRabbit](https://coderabbit.ai) checks tailored to the issues you actually see in practice.

## Usage

Ask your agent to run the skill on the current repository:

> Run the CodeRabbit config generator skill for this repo using the last 90 days of PRs and commits.

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
scripts/run_analysis.sh --repo-path /path/to/repo --repo owner/name
```

## Validating a config

Requires PyYAML (`pip install pyyaml`). The validator warns about label gating and review status messages.

```bash
python3 scripts/validate_coderabbit_yaml.py --config .coderabbit.yaml
```

## Tuning patterns

Edit `scripts/patterns.json` to add or refine keyword and regex matches used during analysis.
