Use the repo-local `context-routing-skill` in `.agents/skills` for this repository.

Produce a minimal `Route Card` now in a single response.

Constraints:
- Do not ask follow-up questions.
- Do not turn this into an execution plan.
- Use repository evidence only.
- Output only these `Route Card` fields, in this exact order:
  - `task_type`
  - `goal`
  - `read_first`
  - `read_next`
  - `code_entry`
  - `do_not_read_yet`
  - `stop_reading_when`
  - `open_questions`
- Use exact repo-relative paths, not prose labels, whenever repository evidence is available.
- Keep `read_next` to the smallest unresolved local dependency trace that explains module boundaries.
- Prefer the shortest file chain that identifies entrypoints and immediate dependencies; do not broaden into secondary scans unless the current evidence cannot explain the local module graph.
- If information is insufficient, still return the `Route Card` and name only the smallest missing entrypoints or dependency edges that block routing.
- If repository evidence is already sufficient, do not add fallback or meta caveats.
- Make `stop_reading_when` explicit and evidence-based so a reader knows when enough routing context has been collected.

I need to work on a task in this repository.

Before I start, I want to understand:
- where I should begin reading
- what files are likely relevant
- what I should avoid reading for now

The task is:
understand local modules and their dependencies

Please output only the `Route Card`.
