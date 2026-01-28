---
name: coderabbit-config-generator
description: Generate .coderabbit.yaml configurations tailored to your project by analyzing PR history, commit patterns, and existing code standards. Use when the user asks to "create coderabbit config", "set up coderabbit", "generate code review rules", or needs automated PR review configuration based on their project's specific patterns and tooling.
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
---

# CodeRabbit Configuration Generator

This skill generates project-specific `.coderabbit.yaml` files by analyzing your repository's PR history, bug patterns, and existing tooling to create custom review rules.

## When to Use

- Setting up CodeRabbit for a new repository
- Migrating from another code review tool
- Updating CodeRabbit config after identifying new bug patterns
- Creating custom checks based on project-specific anti-patterns

## Workflow

### Automated workflow (recommended)

Prerequisites:
- GitHub CLI (`gh`) authenticated
- Local git clone of the repository
- Python 3 on your `PATH`

Run the analyzer scripts bundled with this skill:

```bash
# From the skill directory
scripts/run_analysis.sh --repo-path /path/to/repo --repo owner/name
```

Outputs:
- `analysis/pr-data.json`
- `analysis/commit-log.txt`
- `analysis/pattern-report.json`

Adjust the lookback window or output directory as needed:

```bash
scripts/run_analysis.sh \
  --repo-path /path/to/repo \
  --repo owner/name \
  --days 90 \
  --out-dir analysis
```

To add or tune patterns, edit `scripts/patterns.json`.

### Step 1: Gather PR and Commit History

Collect recent merge history to identify patterns:

```bash
# Get merged PRs from last 2 months with details
gh pr list --state merged --limit 50 --json number,title,body,labels,mergedAt

# Get commit history for pattern analysis
git log --oneline --since="2 months ago" --pretty=format:"%h %s"

# Get PR descriptions that mention bugs or fixes
gh pr list --state merged --limit 50 --json title,body | jq '.[] | select(.title | test("fix|bug|patch|hotfix"; "i"))'
```

### Step 2: Identify Bug Patterns

Look for recurring issues in PR titles and bodies:

| Pattern Keyword | Likely Issue | Custom Check Target |
|-----------------|--------------|---------------------|
| `fix:`, `bug:` | General bugs | Root cause category |
| `shallow copy`, `deepcopy` | Mutable default corruption | Shallow copy mutation |
| `abort`, `cancel`, `cleanup` | Exception path issues | Exception cleanup |
| `state`, `corrupt`, `invalid` | State management bugs | State invariants |
| `type:`, `typing` | Type safety issues | Type annotation checks |
| `frozen`, `immutable` | Mutation of immutables | Frozen object mutation |
| `circular`, `import` | Dependency violations | Import direction |
| `silent`, `swallow` | Error suppression | Silent failure detection |

### Step 3: Read Project Standards

Gather existing configuration and standards:

```bash
# Project coding standards
cat CLAUDE.md 2>/dev/null || cat .github/CONTRIBUTING.md 2>/dev/null

# Python tooling configuration
cat pyproject.toml 2>/dev/null | grep -A 50 "\[tool.ruff\]"
cat pyproject.toml 2>/dev/null | grep -A 20 "\[tool.mypy\]"

# Pre-commit hooks
cat .pre-commit-config.yaml 2>/dev/null

# Existing CodeRabbit config (if updating)
cat .coderabbit.yaml 2>/dev/null
```

### Step 4: Generate Configuration

**CRITICAL CONSTRAINT:** CodeRabbit's schema only allows a maximum of **5 custom_checks** in `pre_merge_checks.custom_checks`. Do not exceed this limit or the config will fail validation.

Prioritize checks based on bug frequency and severity. If more than 5 patterns are identified, either:
- Combine related checks into one
- Use path_instructions for less critical patterns
- Skip style-only checks if pre-commit hooks already cover them

Create `.coderabbit.yaml` with the following structure:

```yaml
# yaml-language-server: $schema=https://coderabbit.ai/integrations/schema.v2.json
language: "en-US"
tone_instructions: "Be direct and technical. Focus on correctness and maintainability."

reviews:
  profile: "chill"  # or "assertive" for stricter reviews
  review_status: true  # Set to false to disable status comments and only trigger via labels/flags

  path_filters:
    - "!**/*.md"
    - "!docs/**"
    - "!**/assets/**"
    - "!**/*.lock"
    - "!**/generated/**"
    - "!**/__pycache__/**"

  path_instructions:
    - path: "src/**/core/**"
      instructions: |
        This is the core business logic. Pay special attention to:
        - State invariants and cleanup in exception paths
        - Dependency direction (core should not import from ui/)
        - Contract violations (preconditions/postconditions)

    - path: "src/**/tools/**"
      instructions: |
        Tool implementations must:
        - Fail fast with clear error messages
        - Never silently return None on errors
        - Validate preconditions explicitly

    - path: "src/**/ui/**"
      instructions: |
        UI code should:
        - Not contain business logic
        - Not import from core/ internals
        - Handle user-facing errors gracefully

  auto_review:
    enabled: true
    drafts: false
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "draft"
    base_branches:
      - "main"
      - "master"
    # labels:  # Uncomment to require specific labels for auto-review
    #   - "needs-review"

  pre_merge_checks:
    custom_checks:
      - name: "Shallow Copy Mutation"
        mode: "error"
        instructions: |
          Flag any code that:
          1. Uses .copy() on a dict/list that contains nested mutable objects
          2. Mutates a copied config dict in-place
          3. Modifies DEFAULT_* or CONSTANT_* values

          Safe alternatives:
          - Use copy.deepcopy() for nested structures
          - Create new dict instead of mutating
          - Assign to new variable, don't mutate in-place

      - name: "Exception Path Cleanup"
        mode: "warning"
        instructions: |
          For any stateful loop or transaction, verify:
          1. All exit paths (normal, exception, early return) leave state valid
          2. try/except blocks that catch mid-operation have cleanup
          3. Resources acquired before exception are released

          Pattern to flag:
          - State mutation followed by operation that can raise
          - No cleanup in except block for stateful operations

      - name: "Silent Failure Detection"
        mode: "error"
        instructions: |
          Flag these anti-patterns:
          1. Bare except: pass
          2. return None without logging on error path
          3. Catching exception and returning empty collection
          4. if not condition: return (without error indication)

          Required: Errors should be raised, logged, or explicitly documented.

      - name: "Dependency Direction"
        mode: "warning"
        instructions: |
          Verify import direction follows: ui -> core -> tools -> utils/types

          Flag violations:
          - core/ importing from ui/
          - tools/ importing from ui/
          - utils/ or types/ importing from higher layers

          Inner layers must not know about outer layers.

      - name: "Magic Number Detection"
        mode: "warning"
        instructions: |
          Flag numeric literals that should be named constants:
          - Timeout values (e.g., 30, 60, 300)
          - Size limits (e.g., 1024, 4096)
          - Retry counts (e.g., 3, 5)
          - Status codes

          Exception: 0, 1, -1 in common idioms are acceptable.

  tools:
    ruff:
      enabled: true
    # mypy:
    #   enabled: true
    # bandit:
    #   enabled: true
    gitleaks:
      enabled: true

knowledge_base:
  code_guidelines:
    filePatterns:
      - "**/*.py"
```

## Configuration Options

### Review Status Messages

By default, `review_status: true` posts a status comment on every PR indicating CodeRabbit is reviewing. To disable these status messages and only trigger reviews via labels or explicit flags, set:

```yaml
reviews:
  review_status: false
```

This is useful for high-volume repos where status messages add noise.

### Label-Gated Reviews

By default, auto_review runs on all PRs. To require specific labels before triggering a review, add:

```yaml
reviews:
  auto_review:
    labels:
      - "needs-review"
```

**Warning:** If labels are configured, PRs without those labels will be skipped with "Review skipped - Auto reviews are limited based on label configuration."

## Custom Check Derivation Guide

**REMEMBER: Maximum 5 custom_checks allowed.** Prioritize by bug severity and frequency.

Based on bug patterns found in Step 2, add appropriate custom checks:

### If Config Corruption Bugs Found

Add "Shallow Copy Mutation" check with mode "error".

### If State Corruption or Abort Bugs Found

Add "Exception Path Cleanup" check. Look for patterns like:
- User abort leaving invalid state
- Transaction incomplete after exception
- Resources not released

### If Pydantic/Dataclass Bugs Found

Add "Frozen Object Mutation" check:

```yaml
- name: "Frozen Object Mutation"
  mode: "error"
  instructions: |
    Flag attempts to modify frozen dataclasses or Pydantic models:
    1. Direct attribute assignment on frozen=True objects
    2. In-place mutation of frozen object's mutable fields
    3. Missing model_copy() for Pydantic v2 modifications
```

### If Type-Related Bugs Found

Add "Type Safety" check:

```yaml
- name: "Type Annotation Gaps"
  mode: "warning"
  instructions: |
    Flag:
    1. Functions without return type annotations
    2. Any/object types without justification
    3. cast() without # type: verified comment
    4. # type: ignore without explanation
```

## File Placement

The generated file MUST be named `.coderabbit.yaml` (with leading dot) and placed in the repository root.

## Validation

After generating, validate the configuration:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.coderabbit.yaml'))"

# CRITICAL: Verify custom_checks count (max 5 allowed by CodeRabbit schema)
grep -A 1 "custom_checks:" .coderabbit.yaml | grep -c "name:" || true
# If output > 5, remove or consolidate checks

# Verify custom check name lengths (must be under 50 chars)
grep "name:" .coderabbit.yaml | awk -F'"' '{print length($2), $2}' | awk '$1 > 50'
```

## Example: Analyzing Bug Patterns

Given these PR titles from history:

```
fix: shallow copy corrupts DEFAULT_USER_CONFIG
fix: dangling tool calls on user abort
fix: state manager not cleaning up on exception
```

The generator would add these checks with mode "error":
1. Shallow Copy Mutation
2. Exception Path Cleanup

(Leaving room for 3 more checks if needed - max 5 total)

And set path_instructions for core/ and tools/ to emphasize state management.

## Output

The skill produces:
1. `.coderabbit.yaml` in repository root
2. Summary of bug patterns that informed the configuration
3. Recommendations for additional custom checks based on project structure
