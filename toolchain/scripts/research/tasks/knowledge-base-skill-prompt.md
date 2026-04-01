Use the repo-local `knowledge-base-skill` in `.claude/skills` for this repository.

Produce the Knowledge Base assessment now in a single response.

Constraints:
- Do not ask follow-up questions.
- Use repository evidence only.
- If evidence is incomplete, make that explicit and still return the smallest safe assessment.
- Focus on documentation structure, mainline entrypoints, missing or broken links, and the smallest safe doc updates.
- Do not propose a broad rewrite unless the repository state clearly requires it.
- Distinguish documentation layers from navigation entrypoints. Do not classify `README.md`, `INDEX.md`, `AGENTS.md`, or other entry files as part of a truth layer unless the repository explicitly defines them that way.
- Distinguish primary mainline entrypoints from task-specific or secondary entrypoints. If you name entrypoints, prefer the smallest verified primary set first.
- If the repository defines an agent-facing entrypoint such as `AGENTS.md`, include it when relevant instead of silently omitting it.
- Do not claim that no mainline entrypoints are missing or broken unless you inspected the primary root and docs entrypoints needed to support that claim.
- If evidence is only partial, say so explicitly instead of inferring missing structure from generic documentation patterns.

I want to improve the documentation of this repository so that it is easier for both humans and AI to understand and navigate.

Right now, I’m not sure:
- whether the documentation structure is complete
- which documents are missing or outdated
- what should be considered the main entry points

Please output only:
- the current mode: `Bootstrap` or `Adopt`
- the current layer classification
- the missing or broken mainline entrypoints
- the smallest safe doc updates required
