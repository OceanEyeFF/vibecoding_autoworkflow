## Autoresearch P2 Claude-Claude Template Bundle

This bundle is a copy-ready starting point for one minimal P2 autoresearch run that:

- mutates exactly one research prompt file
- uses `claude` as the worker backend
- uses `claude` as both suite backend and judge backend

Files:

- `contract.template.json`
- `train.template.yaml`
- `validation.template.yaml`
- `acceptance.template.yaml`
- `manual-mutation.template.json`

Typical usage:

1. Copy these files into a run-local directory under `.autoworkflow/manual-runs/`.
2. Rename them to `contract.json`, `train.yaml`, `validation.yaml`, `acceptance.yaml`, and `manual-mutation.json`.
3. Replace `/abs/path/to/target-repo` in the suite files with the repository you want to evaluate.
4. Refresh the contract `run_id` before the run:

```bash
python3 autoresearch/src/refresh_manual_run_contract.py \
  --contract /abs/path/to/contract.json
```

The template defaults to the `context-routing-skill` prompt target. If you switch to another P2 task, update these fields together:

- `target_task`
- `target_prompt_path`
- `mutable_paths`
- `manual-mutation.template.json` `target_paths`
