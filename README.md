# CodeRabbit Config Generator Skill

## Where
This repository is a standalone Pi skill. The skill definition lives in `SKILL.md` and the helper scripts live in `scripts/`.

## What
The skill analyzes recent GitHub pull requests and local commit history to identify recurring bug patterns. It then recommends CodeRabbit custom checks based on those patterns.

## Why
Recurring issues should drive review automation. This skill turns common failure modes into repeatable CodeRabbit checks so reviews focus on high-risk changes.

## How

### Prerequisites
- GitHub CLI (`gh`) authenticated
- Python 3
- Local git clone of the repository you want to analyze

### Quickstart
```bash
scripts/run_analysis.sh --repo-path /path/to/repo --repo owner/name
```

### Outputs
- `analysis/pr-data.json`
- `analysis/commit-log.txt`
- `analysis/pattern-report.json`

### Customize patterns
Edit `scripts/patterns.json` to add or tune keyword and regex matches.
