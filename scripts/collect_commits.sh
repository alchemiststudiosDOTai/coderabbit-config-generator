#!/usr/bin/env bash
set -euo pipefail

print_usage() {
  cat <<'USAGE'
Usage: scripts/collect_commits.sh [options]

Options:
  --repo-path PATH    Local repository path (required)
  --days N            Look back N days (default: 90)
  --out PATH          Output text path (default: commit-log.txt)
  -h, --help          Show this help text
USAGE
}

DAYS=90
OUT="commit-log.txt"
REPO_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-path)
      REPO_PATH="$2"
      shift 2
      ;;
    --days)
      DAYS="$2"
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

if [[ -z "${REPO_PATH}" ]]; then
  echo "--repo-path is required." >&2
  print_usage >&2
  exit 1
fi

if [[ ! -d "${REPO_PATH}/.git" ]]; then
  echo "No .git directory found at ${REPO_PATH}" >&2
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

OUT_DIR=$(dirname "${OUT}")
if [[ "${OUT_DIR}" != "." ]]; then
  mkdir -p "${OUT_DIR}"
fi

git -C "${REPO_PATH}" log \
  --since="${SINCE_DATE}" \
  --pretty=format:"%h %s" \
  > "${OUT}"

echo "Wrote commit log to ${OUT}"
