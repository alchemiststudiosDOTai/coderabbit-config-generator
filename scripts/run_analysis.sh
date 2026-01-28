#!/usr/bin/env bash
set -euo pipefail

print_usage() {
  cat <<'USAGE'
Usage: scripts/run_analysis.sh [options]

Options:
  --repo OWNER/NAME   GitHub repository (optional if derived from origin)
  --repo-path PATH    Local repository path (required)
  --days N            Look back N days (default: 90)
  --limit N           Max PRs to fetch (default: 200)
  --out-dir PATH      Output directory (default: analysis)
  -h, --help          Show this help text
USAGE
}

DAYS=90
LIMIT=200
OUT_DIR="analysis"
REPO=""
REPO_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --repo-path)
      REPO_PATH="$2"
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
    --out-dir)
      OUT_DIR="$2"
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

if [[ -z "${REPO}" ]]; then
  ORIGIN_URL=$(git -C "${REPO_PATH}" remote get-url origin 2>/dev/null || true)
  if [[ "${ORIGIN_URL}" =~ github.com[:/](.+/[^/.]+)(\.git)?$ ]]; then
    REPO="${BASH_REMATCH[1]}"
  fi
fi

if [[ -z "${REPO}" ]]; then
  echo "Could not derive GitHub repo. Provide --repo OWNER/NAME." >&2
  exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

mkdir -p "${OUT_DIR}"

PR_JSON="${OUT_DIR}/pr-data.json"
COMMIT_LOG="${OUT_DIR}/commit-log.txt"
REPORT_JSON="${OUT_DIR}/pattern-report.json"

"${SCRIPT_DIR}/collect_prs.sh" \
  --repo "${REPO}" \
  --days "${DAYS}" \
  --limit "${LIMIT}" \
  --out "${PR_JSON}"

"${SCRIPT_DIR}/collect_commits.sh" \
  --repo-path "${REPO_PATH}" \
  --days "${DAYS}" \
  --out "${COMMIT_LOG}"

python3 "${SCRIPT_DIR}/analyze_patterns.py" \
  --pr-json "${PR_JSON}" \
  --commit-log "${COMMIT_LOG}" \
  --json-out "${REPORT_JSON}"

echo "Analysis complete. See ${OUT_DIR}/pattern-report.json"
