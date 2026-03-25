Use the repo-local `writeback-cleanup-skill` in `.claude/skills` for this repository.

Produce a minimal `Writeback Card` now in a single response.

Constraints:
- Do not ask follow-up questions.
- Use available repository evidence only. Use git history only if it is actually needed.
- If verification is insufficient, say so explicitly in the card instead of guessing.
- Focus on documentation updates, stale assumptions, stale entrypoints, and cleanup targets.
- Do not turn this into a full repository audit.

I’ve just completed a task in this repository. You need to help me clean up the documentation.

Some parts of the system have changed, and some previous assumptions or notes may no longer be accurate.

You may need to use git commands to review previous commits.

I want to:
- make sure the important changes are properly documented
- avoid keeping outdated or misleading information
- keep the documentation clean and reliable

Please output only the `Writeback Card`.
