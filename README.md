# CodeRabbit Config Generator (Skill)

Use this skill to turn your project’s recent PR history and commit messages into CodeRabbit checks that match the issues you actually see in practice. It surfaces recurring problems, highlights rare edge cases, and recommends custom checks that keep reviews focused on real risks.

## Quickstart (skill)
Ask your agent to run the skill on the current repository, for example:

"Run the CodeRabbit config generator skill for this repo using the last 90 days of PRs and commits."

## Prerequisites
- GitHub CLI (`gh`) authenticated
- Python 3
- A local git clone of the repository you want to analyze

## Optional: run the scripts directly
```bash
scripts/run_analysis.sh --repo-path /path/to/repo --repo owner/name
```

## What you get
- `analysis/pr-data.json`
- `analysis/commit-log.txt`
- `analysis/pattern-report.json`

## Tune the patterns
Edit `scripts/patterns.json` to add or refine keyword and regex matches.
