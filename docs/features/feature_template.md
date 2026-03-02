# Feature: [Feature Name]

> **GitHub Issue:** `#NNN`
> **Status:** `planned` | `in-progress` | `complete`
> **Module:** `document_simulator.[subsystem].[module]`

---

## Summary

One or two sentences describing what this feature does and what problem it solves.

---

## Motivation

### Problem Statement

What gap or pain point does this feature address? Why does it need to exist in this system?

### Value Delivered

- Bullet list of concrete benefits to users or downstream subsystems.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| [user type] | I can [action] | [outcome / benefit] |
| [user type] | I can [action] | [outcome / benefit] |

---

## Acceptance Criteria

All criteria must be verifiable by an automated test or a manual step that a reviewer can reproduce.

- [ ] AC-1: [Specific, testable outcome]
- [ ] AC-2: [Specific, testable outcome]
- [ ] AC-3: [Specific, testable outcome]

---

## Design

### Public API

The stable, user-facing surface of this feature. Changes here are breaking changes.

```python
# Python API
from document_simulator.[subsystem] import [ClassName or function]

result = [ClassName or function]([args])
```

```bash
# CLI (if applicable)
uv run python -m document_simulator [subcommand] [args]
```

### Data Flow

```
[Input]
    │
    ▼
[Step 1: description]
    │
    ▼
[Step 2: description]
    │
    ▼
[Output: shape / type / format]
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `ClassName` | class | [one-line description] |
| `function_name(args)` | function | [one-line description] |
| `DataModel` | dataclass/Pydantic | [one-line description] |

### Configuration

Settings exposed via `.env` / `Settings` (Pydantic):

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `SETTING_NAME` | `bool` | `false` | [description] |

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/[path].py` | [Primary implementation] |
| `src/document_simulator/[path].py` | [Supporting module] |

### Key Architectural Decisions

1. **[Decision title]** — [Rationale. What alternatives were considered and why this was chosen.]
2. **[Decision title]** — [Rationale.]

### Known Edge Cases & Constraints

- [Edge case or known limitation]
- [Performance constraint or hardware requirement]

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/[path].py` | unit | N | [scope] |
| `tests/[path].py` | integration | N | [scope] |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_[name]` | `tests/[path].py` | `[ImportError / AttributeError / AssertionError: ...]` |
| `test_[name]` | `tests/[path].py` | `[ImportError / AttributeError / AssertionError: ...]` |

**Green — minimal implementation:**

Describe the smallest code change that turned all red tests green. Call out any shortcuts taken that were intentional (e.g., hard-coded return values, no error handling yet).

```
[class / function stub or key diff — optional but encouraged]
```

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| [e.g., extracted helper function] | [e.g., duplicated logic across two methods] |
| [e.g., replaced dict with Pydantic model] | [e.g., needed validation and serialisation] |

Note any tests that were added *after* the refactor to cover the new structure.

### How to Run

```bash
# All tests for this feature
uv run pytest tests/[path] -v

# Single test
uv run pytest tests/[path]::test_[name] -v

# With coverage
uv run pytest tests/[path] --cov=document_simulator.[module]
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `[package or module]` | external / internal | [reason] |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| `[module or page]` | [brief description] |

---

## Usage Examples

### Minimal

```python
# Shortest working example
```

### Typical

```python
# Representative real-world usage
```

### Advanced / Edge Case

```python
# Non-obvious usage or boundary condition
```

---

## Future Work

- [ ] [Planned enhancement or known gap]
- [ ] [Planned enhancement or known gap]

---

## References

- [Link to relevant plan or research doc](../[file].md)
- [External library docs if key to this feature]
