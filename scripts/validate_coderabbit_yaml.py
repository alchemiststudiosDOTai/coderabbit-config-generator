#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Config must be a YAML mapping at the top level.")
    return data


def ensure_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def validate_custom_checks(
    config: Dict[str, Any],
    max_checks: int,
    max_name_length: int,
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    reviews = ensure_mapping(config.get("reviews"))
    pre_merge = ensure_mapping(reviews.get("pre_merge_checks"))
    custom_checks = pre_merge.get("custom_checks", [])

    if custom_checks is None:
        custom_checks = []

    if not isinstance(custom_checks, list):
        errors.append("reviews.pre_merge_checks.custom_checks must be a list.")
        return errors, warnings

    if len(custom_checks) > max_checks:
        errors.append(
            f"custom_checks has {len(custom_checks)} entries (max {max_checks})."
        )

    for index, check in enumerate(custom_checks, start=1):
        if not isinstance(check, dict):
            errors.append(f"custom_checks[{index}] must be a mapping.")
            continue
        name = check.get("name", "")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"custom_checks[{index}] is missing a name.")
            continue
        if len(name) > max_name_length:
            errors.append(
                f"custom_checks[{index}] name is {len(name)} characters (max {max_name_length})."
            )

    auto_review = ensure_mapping(reviews.get("auto_review"))
    labels = auto_review.get("labels", [])
    if isinstance(labels, list) and labels:
        warnings.append(
            "auto_review.labels is set. CodeRabbit will require at least one label on each PR."
        )

    review_status = reviews.get("review_status")
    if review_status is True:
        warnings.append(
            "reviews.review_status is true. CodeRabbit will post review status messages."
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a .coderabbit.yaml file.")
    parser.add_argument(
        "--config",
        default=".coderabbit.yaml",
        help="Path to the CodeRabbit YAML config",
    )
    parser.add_argument("--max-custom-checks", type=int, default=5)
    parser.add_argument("--max-name-length", type=int, default=50)
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    try:
        config = load_yaml(config_path)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    errors, warnings = validate_custom_checks(
        config,
        max_checks=args.max_custom_checks,
        max_name_length=args.max_name_length,
    )

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("Errors:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
