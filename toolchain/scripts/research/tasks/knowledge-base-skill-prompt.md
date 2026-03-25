Use the repo-local `knowledge-base-skill` in `.claude/skills` for this repository.

Produce the Knowledge Base assessment now in a single response.

Constraints:
- Do not ask follow-up questions.
- Use repository evidence only.
- If evidence is incomplete, make that explicit and still return the smallest safe assessment.
- Focus on documentation structure, mainline entrypoints, missing or broken links, and the smallest safe doc updates.
- Do not propose a broad rewrite unless the repository state clearly requires it.

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
