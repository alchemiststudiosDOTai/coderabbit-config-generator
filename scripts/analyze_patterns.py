#!/usr/bin/env python3
import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


@dataclass
class CompiledPattern:
    pattern_id: str
    label: str
    issue: str
    recommended_check: str
    severity: str
    regexes: List[re.Pattern]


@dataclass
class PatternStats:
    pattern: CompiledPattern
    pr_numbers: Set[int] = field(default_factory=set)
    commit_hashes: Set[str] = field(default_factory=set)

    def total_matches(self) -> int:
        return len(self.pr_numbers) + len(self.commit_hashes)


def load_patterns(path: Path) -> List[CompiledPattern]:
    data = json.loads(path.read_text())
    patterns = []
    for item in data.get("patterns", []):
        regexes = []
        for keyword in item.get("keywords", []):
            if not keyword:
                continue
            regexes.append(re.compile(re.escape(keyword), re.IGNORECASE))
        for regex in item.get("regexes", []):
            if not regex:
                continue
            regexes.append(re.compile(regex, re.IGNORECASE))
        patterns.append(
            CompiledPattern(
                pattern_id=item.get("id", ""),
                label=item.get("label", ""),
                issue=item.get("issue", ""),
                recommended_check=item.get("recommended_check", ""),
                severity=item.get("severity", ""),
                regexes=regexes,
            )
        )
    return patterns


def load_prs(path: Path) -> Iterable[Dict[str, object]]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("PR JSON must be a list of PR objects.")
    return raw


def load_commit_log(path: Path) -> Iterable[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def match_patterns(text: str, patterns: List[CompiledPattern]) -> List[CompiledPattern]:
    matches = []
    for pattern in patterns:
        if any(regex.search(text) for regex in pattern.regexes):
            matches.append(pattern)
    return matches


def scan_prs(prs: Iterable[Dict[str, object]], stats: Dict[str, PatternStats]) -> None:
    for pr in prs:
        title = str(pr.get("title") or "")
        body = str(pr.get("body") or "")
        text = f"{title}\n{body}"
        for pattern in match_patterns(text, [s.pattern for s in stats.values()]):
            number = pr.get("number")
            if isinstance(number, int):
                stats[pattern.pattern_id].pr_numbers.add(number)


def scan_commits(lines: Iterable[str], stats: Dict[str, PatternStats]) -> None:
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) < 2:
            continue
        commit_hash, subject = parts[0], parts[1]
        for pattern in match_patterns(subject, [s.pattern for s in stats.values()]):
            stats[pattern.pattern_id].commit_hashes.add(commit_hash)


def format_examples(items: Iterable[str], max_items: int) -> str:
    items_list = list(items)
    if not items_list:
        return ""
    clipped = items_list[:max_items]
    suffix = "" if len(items_list) <= max_items else f" (+{len(items_list) - max_items} more)"
    return ", ".join(clipped) + suffix


def render_report(
    stats: List[PatternStats],
    recurring_threshold: int,
    max_examples: int,
) -> str:
    recurring = []
    edge = []
    for item in stats:
        total = item.total_matches()
        if total >= recurring_threshold:
            recurring.append(item)
        elif total > 0:
            edge.append(item)

    lines = []
    lines.append("Pattern analysis summary")
    lines.append("------------------------")

    if recurring:
        lines.append("Recurring issues")
        for item in recurring:
            pr_examples = format_examples([f"#{n}" for n in sorted(item.pr_numbers)], max_examples)
            commit_examples = format_examples(sorted(item.commit_hashes), max_examples)
            details = []
            if pr_examples:
                details.append(f"PRs: {pr_examples}")
            if commit_examples:
                details.append(f"Commits: {commit_examples}")
            detail_text = "; ".join(details) if details else "No examples captured"
            lines.append(
                f"- {item.pattern.label} ({item.total_matches()} matches) :: {item.pattern.issue}. {detail_text}"
            )
    else:
        lines.append("Recurring issues")
        lines.append("- None detected")

    if edge:
        lines.append("")
        lines.append("Edge cases")
        for item in edge:
            pr_examples = format_examples([f"#{n}" for n in sorted(item.pr_numbers)], max_examples)
            commit_examples = format_examples(sorted(item.commit_hashes), max_examples)
            details = []
            if pr_examples:
                details.append(f"PRs: {pr_examples}")
            if commit_examples:
                details.append(f"Commits: {commit_examples}")
            detail_text = "; ".join(details) if details else "No examples captured"
            lines.append(
                f"- {item.pattern.label} ({item.total_matches()} matches) :: {item.pattern.issue}. {detail_text}"
            )

    suggested_checks = sorted(
        {item.pattern.recommended_check for item in recurring if item.pattern.recommended_check}
    )
    lines.append("")
    lines.append("Suggested custom checks")
    if suggested_checks:
        for check in suggested_checks:
            lines.append(f"- {check}")
    else:
        lines.append("- None suggested (no recurring issues detected)")

    return "\n".join(lines)


def build_stats(patterns: List[CompiledPattern]) -> Dict[str, PatternStats]:
    return {pattern.pattern_id: PatternStats(pattern=pattern) for pattern in patterns}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze PRs and commits for recurring bug patterns.")
    parser.add_argument("--pr-json", help="Path to PR JSON from collect_prs.sh")
    parser.add_argument("--commit-log", help="Path to commit log from collect_commits.sh")
    parser.add_argument(
        "--patterns",
        default=str(Path(__file__).with_name("patterns.json")),
        help="Pattern definition JSON",
    )
    parser.add_argument("--recurring-threshold", type=int, default=3)
    parser.add_argument("--max-examples", type=int, default=5)
    parser.add_argument("--json-out", help="Write JSON report to path")
    args = parser.parse_args()

    if not args.pr_json and not args.commit_log:
        print("Provide --pr-json, --commit-log, or both.", file=sys.stderr)
        return 1

    patterns = load_patterns(Path(args.patterns))
    stats = build_stats(patterns)

    if args.pr_json:
        scan_prs(load_prs(Path(args.pr_json)), stats)
    if args.commit_log:
        scan_commits(load_commit_log(Path(args.commit_log)), stats)

    stats_list = list(stats.values())
    report = render_report(stats_list, args.recurring_threshold, args.max_examples)
    print(report)

    if args.json_out:
        report_data = {
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "recurring_threshold": args.recurring_threshold,
            "patterns": [
                {
                    "id": item.pattern.pattern_id,
                    "label": item.pattern.label,
                    "issue": item.pattern.issue,
                    "recommended_check": item.pattern.recommended_check,
                    "severity": item.pattern.severity,
                    "pr_numbers": sorted(item.pr_numbers),
                    "commit_hashes": sorted(item.commit_hashes),
                    "total_matches": item.total_matches(),
                }
                for item in stats_list
            ],
        }
        Path(args.json_out).write_text(json.dumps(report_data, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
