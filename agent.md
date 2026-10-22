# Agent configuration

This repository uses a lightweight engineering workflow for scoped, verifiable changes.

## Objectives
- Keep changes surgical and focused on the user request.
- Prefer the smallest validation command that checks the changed behavior.
- Preserve existing behavior unless the task explicitly requires a change.

## Workflow
1. Inspect the relevant files and the failing behavior before editing.
2. Make the minimal code change needed to address the root cause.
3. Validate with the smallest relevant command or test target.
4. Summarize the change and verification clearly.

## Constraints
- Do not make unrelated refactors or broad cleanup.
- Do not add new dependencies unless explicitly required.
- Do not commit unless the user asks for it.
- Prefer direct, precise edits over large rewrites.

## Preferred validation
- Use project-local scripts or existing tests when available.
- If no project test harness exists, validate through the smallest direct execution or static check.
- Report any inability to validate honestly and include the command attempted.
