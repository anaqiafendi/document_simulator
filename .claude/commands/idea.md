# Idea intake — research, plan, document, implement

You are the intake agent for a new idea, experiment, or feature request. Your job is to take the raw idea in `$ARGUMENTS` and drive it all the way from a rough description to a merged pull request, following the project's FDD workflow.

Work through every phase below in order. Do not skip phases. At the start of each phase, state which phase you are entering so the user can follow along.

---

## Phase 0 — Understand the idea

Parse `$ARGUMENTS` as the raw idea description. If it is empty, ask the user:
> "What is the idea you want to explore? Describe it in as much detail as you have — even rough notes are fine."

Before proceeding, briefly restate the idea in your own words and ask the user to confirm or correct it. Keep this exchange to one round — do not loop.

Also determine:
- **Type:** new feature / enhancement to existing feature / experiment / refactor / bug fix
- **Likely scope:** which module(s) or UI page(s) are involved (make a best guess from the codebase structure in `src/document_simulator/`)
- **Target branch:** the branch the new feature branch should be cut from. Default order of preference: `dev` if it exists → `main`. If the idea clearly builds on a specific in-progress feature branch, use that instead.

---

## Phase 1 — Create the feature branch

Run in sequence:

```bash
# Confirm available branches
git branch -a

# Check out the target branch and pull latest
git checkout [target-branch] && git pull

# Create the feature branch
git checkout -b feature/[kebab-case-slug-derived-from-idea]
```

The branch name must:
- Start with `feature/`
- Be lowercase kebab-case
- Be concise but descriptive (3–6 words max)
- Not duplicate an existing branch name

Report the branch name created before moving on.

---

## Phase 2 — Research

Spawn a **research sub-agent** with the following instructions:

> Research how to implement: [full idea description]
>
> Context:
> - Project: document_simulator — a Python system for document augmentation, OCR, and RL pipeline optimisation
> - Package manager: uv. Python 3.11. Main package under `src/document_simulator/`.
> - Existing dependencies: see `pyproject.toml`
> - Existing patterns: read `docs/features/feature_template.md` and two or three existing feature docs in `docs/features/` to understand conventions
>
> Produce a structured research summary covering:
> 1. Existing solutions / libraries that could be reused (with licences)
> 2. Relevant patterns already present in this codebase
> 3. Known gotchas, performance considerations, or compatibility constraints
> 4. Recommended implementation approach with rationale
> 5. Alternatives considered and why they are inferior
>
> Write the findings to `docs/RESEARCH_FINDINGS.md` (append a dated section, do not overwrite).

Wait for the research sub-agent to finish before proceeding.

---

## Phase 3 — Plan

Spawn a **planning sub-agent** with the following instructions:

> Using the research findings just appended to `docs/RESEARCH_FINDINGS.md`, produce a detailed implementation plan for: [full idea description]
>
> The plan must cover:
> 1. Files to create or modify (with a one-line description of the change for each)
> 2. Public API design — function/class signatures, return types, Pydantic models
> 3. Data flow diagram (ASCII is fine)
> 4. TDD test plan — for each piece of behaviour, name the test, the file it lives in, and the initial failure reason (Red step)
> 5. Acceptance criteria — each must be specific and verifiable by an automated test or a reproducible manual step
> 6. Dependencies to add (if any) and why
> 7. Risks and open questions
>
> Return the plan as a structured markdown document. Do not write any code yet.

Wait for the planning sub-agent to finish and collect its output before proceeding.

---

## Phase 4 — Write the FDD

Using the research summary and the plan, create a new FDD file at:

```
docs/features/feature_[snake_case_slug].md
```

The file must follow `docs/features/feature_template.md` exactly. Fill every section:
- **Status:** `in-progress`
- **Summary, Motivation, User Stories** — derived from the idea and research
- **Acceptance Criteria** — use the ACs from the plan, all unchecked `- [ ]`
- **Design** — Public API, Data Flow, Key Interfaces, Configuration from the plan
- **Implementation** — Files table and Key Architectural Decisions from the plan; leave `### Bugs Fixed Post-Implementation` with the placeholder `None.`
- **Tests** — Test Files table from the TDD test plan; TDD Cycle Summary with Red/Green/Refactor structure; leave counts as `TBD` until implementation
- **Dependencies** — from the plan
- **Usage Examples** — at least one minimal example
- **Future Work** — open questions and deferred enhancements from the plan

Then add the feature to `docs/features/README.md`:
- Determine the correct section (Core Backend / UI / Synthesis / or add a new section if needed)
- Use the next sequential feature number
- Status: `in-progress`

Commit both files:

```bash
git add docs/features/feature_[slug].md docs/features/README.md docs/RESEARCH_FINDINGS.md
git commit -m "docs: add FDD and research for [feature name]"
```

---

## Phase 5 — Implement

Spawn a **coding sub-agent** with the following instructions:

> Implement the feature described in `docs/features/feature_[slug].md` following strict Red-Green-Refactor TDD.
>
> Rules:
> - Write the first failing test before writing any implementation code (Red)
> - Write the minimum code to make it pass (Green)
> - Refactor only after green — do not over-engineer
> - Follow all conventions in `CLAUDE.md` (type hints, Google docstrings, loguru logging, Pydantic models, uv for all commands)
> - Do not add features, error handling, or abstractions beyond what the ACs require
> - Run `uv run pytest [relevant test paths] -q --no-cov` after each Green step to confirm nothing regressed
> - If you discover a bug or a requirement that was not in the FDD, fix it and note it — do NOT silently work around it
>
> After all ACs are green, run the full test suite:
> ```bash
> uv run pytest tests/ -q --no-cov 2>&1 | tail -10
> ```
> and report the result.

Wait for the coding sub-agent to complete before proceeding.

---

## Phase 6 — Post-implementation FDD update

After implementation is complete:

- If this is a **new feature**: run `/update-fdd` to mark the FDD complete, check off ACs, document bugs, add refined ACs, and add the signoff table.
- If this idea **touched an existing feature** (modified files owned by another FDD): run `/update-fdd [existing_feature_fdd_filename]` for each affected FDD.

---

## Phase 7 — Push and open a pull request

Run in sequence:

```bash
# Push the branch
git push -u origin feature/[slug]

# Open the PR
gh pr create \
  --title "[concise title under 70 chars]" \
  --base [target-branch] \
  --body "$(cat <<'EOF'
## Summary
[3–5 bullet points describing what was built and why]

## Changes
[Bullet list of files added or modified with one-line descriptions]

## Acceptance Criteria
[Copy the checked-off AC list from the FDD]

## Test plan
- [ ] `uv run pytest tests/ -q --no-cov` passes
- [ ] FDD status is `complete` with signoff table
- [ ] No regressions in existing test suite

## FDD
[Link to the feature doc: `docs/features/feature_[slug].md`]
EOF
)"
```

Return the PR URL to the user.

---

## Phase 8 — Report

Print a final summary:

```
Idea: [restated idea title]
Branch: feature/[slug]
FDD: docs/features/feature_[slug].md
PR: [URL]

Phases completed:
  [x] 0 — Idea understood and confirmed
  [x] 1 — Branch created from [target-branch]
  [x] 2 — Research completed
  [x] 3 — Plan produced
  [x] 4 — FDD written and committed
  [x] 5 — Implementation complete (N tests passing)
  [x] 6 — FDD updated and signed off
  [x] 7 — PR opened

Open questions / deferred work:
  [list any items from Future Work section of FDD]
```
