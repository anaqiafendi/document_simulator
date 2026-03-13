# Update FDD after feature signoff

You are finalising Feature Design Documentation (FDD) to reflect the completed, tested, and signed-off state of a feature. Work through the steps below in order without skipping any.

---

## Step 1 — Identify the feature

Run the following commands in parallel:

```bash
git branch --show-current
git log main..HEAD --oneline
```

Map the branch name to the FDD file:
- Branch `feature/foo-bar-baz` → `docs/features/feature_foo_bar_baz.md`
- If the branch name does not map cleanly, scan `docs/features/` for the closest matching filename.

If `$ARGUMENTS` is non-empty it overrides the branch-derived filename (e.g. `/update-fdd feature_ui_ocr_engine`).

---

## Step 2 — Gather context

Run all of the following in parallel:

```bash
# Full diff of everything this branch changed
git diff main...HEAD -- src/ tests/ docs/

# Current test results and counts for this feature's test files
uv run pytest tests/ -q --no-cov 2>&1 | tail -10
```

Also read:
- The FDD file identified in Step 1 (full content).
- `docs/features/README.md` (full content).

---

## Step 3 — Update the FDD file

Apply every change below. Do NOT rewrite the whole document — use targeted edits.

### 3a. Header status
Change the `Status:` line to `complete`.

### 3b. Acceptance Criteria
For each `- [ ] AC-N:` entry, change it to `- [x] AC-N:` if the git diff shows the criterion is satisfied.
If a criterion is genuinely not yet met, leave it unchecked and append `*(not met — [reason])*` inline.

Then review the git diff and bug fixes for requirements that emerged during implementation but are not yet captured as ACs. For each one found, append a new entry after the last existing AC:

```
- [x] AC-N: [Precise, testable statement of the requirement that was discovered/refined]
  > *Refined during implementation: [one sentence explaining what triggered this — e.g. the bug it was exposed by, the constraint discovered, or the edge case that required handling]*
```

Criteria worth adding include:
- A constraint that had to be enforced to prevent a bug (e.g. "parameter name must not have a leading underscore")
- A behavioural rule that was implicit but is now explicit (e.g. "no manual rerun after data_editor write-back")
- An invariant that a regression test was written to protect
- A scope or ordering requirement discovered only during testing
- Update any acceptance criteria that had to be modified as part of enhancements or implementation that emerged
- Remove any acceptance criteria that was determined to be conflicting at a functional level with the feature implementation (rare but happens)

Do NOT add trivial restatements of the original ACs. Each new entry must describe something genuinely absent from the original list.

### 3c. Test Files table
Update the `Count` column in the `### Test Files` table to reflect the actual number of test functions currently in each file (count `def test_` occurrences).
Add any test files present in the git diff that are not yet listed.

### 3d. Bugs Fixed Post-Implementation
Locate the `### Bugs Fixed Post-Implementation` section (it may be inside `## Implementation`).
- If the section does not exist, insert it as the last subsection inside `## Implementation`, just before the closing `---`.
- For each commit whose message starts with `fix:` (or whose summary clearly describes a defect correction), add a numbered bug entry using this structure:

  ```
  **Bug N — [short title from commit message]**

  - **Symptom:** [what the user observed]
  - **Root cause:** [why it happened]
  - **Fix:** [what was changed]
  - **Regression test:** `[test function name]` or "none"
  ```

- If no bugs were fixed, write a single line: `None.`

### 3e. Signoff section
Add (or replace) a `## Signoff` section immediately before `## References` (or at the end of the file if there is no References section):

```markdown
## Signoff

| Date | Branch | Tests passing | Notes |
|------|--------|--------------|-------|
| YYYY-MM-DD | [branch-name] | N | All ACs met |
```

Fill in today's date (`git log -1 --format=%ci HEAD | cut -c1-10` gives a good date), the branch name, and the passing test count from Step 2.

---

## Step 4 — Update `docs/features/README.md`

Check whether the feature already appears in the index table.

- If it is missing, add a row to the correct section ("Core Backend", "UI", or "Synthesis") using the next sequential feature number and status `complete`.
- If it is already present, ensure the status cell reads `complete`.

---

## Step 5 — Report

After all edits are saved, print a concise summary:

```
FDD updated: docs/features/[filename].md
  - Status set to: complete
  - ACs checked off: N / total (+ N refined ACs added)
  - Bugs documented: N
  - README.md: [updated | already current]
  - Tests passing at signoff: N
```
