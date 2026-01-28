#!/usr/bin/env bash
set -euo pipefail

print_usage() {
  cat <<'USAGE'
Usage: scripts/collect_prs.sh [options]

Options:
  --repo OWNER/NAME   GitHub repository to query (optional if in repo context)
  --days N            Look back N days (default: 90)
  --limit N           Max PRs to fetch (default: 200)
  --out PATH          Output JSON path (default: pr-data.json)
  -h, --help          Show this help text
USAGE
}

DAYS=90
LIMIT=200
OUT="pr-data.json"
REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --days)
      DAYS="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --out)
      OUT="$2"
      shift 2
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      print_usage >&2
      exit 1
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required but not installed." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not installed." >&2
  exit 1
fi

SINCE_DATE=$(python3 - <<'PY'
import datetime
import sys

try:
    days = int(sys.argv[1])
except (IndexError, ValueError):
    days = 90

since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
print(since.strftime("%Y-%m-%d"))
PY
"${DAYS}")

REPO_ARGS=()
if [[ -n "${REPO}" ]]; then
  REPO_ARGS=(--repo "${REPO}")
fi

OUT_DIR=$(dirname "${OUT}")
if [[ "${OUT_DIR}" != "." ]]; then
  mkdir -p "${OUT_DIR}"
fi

gh pr list \
  --state merged \
  --search "merged:>${SINCE_DATE}" \
  --limit "${LIMIT}" \
  --json number,title,body,labels,mergedAt,url \
  "${REPO_ARGS[@]}" \
  > "${OUT}"

echo "Wrote PR data to ${OUT}"
