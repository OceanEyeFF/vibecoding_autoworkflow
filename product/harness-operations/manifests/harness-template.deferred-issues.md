# Harness Template Deferred Issues

This file records harness-template issues that have been confirmed but are intentionally deferred until the next harness contract/runtime adjustment pass.

## Deferred: backfill_gate hard-codes pending/scope_gate/passed

- Affected file: `product/harness-operations/manifests/harness.template.yaml`
- Current template command:
  `python3 toolchain/scripts/test/gate_status_backfill.py --workflow-id pending --gate scope_gate --status passed --state-file .autoworkflow/state/harness-review-loop.json --closeout-root .autoworkflow/closeout`
- Introduced in: `7bae746` (`feat(harness): add runtime init foundation`)
- Later locked by test in: `a92c9a2` (`feat(harness): add scope-aware template gates`)
- Current decision: defer fix until the next harness runtime / manifest contract adjustment

### Why this is a bug

`gate_status_backfill.py` only reads `workflow-id`, `gate`, and `status` from CLI args. When the template hard-codes those values:

- every backfill writes into `closeout/pending/`
- every backfill records `scope_gate`
- every backfill records `passed`

That means later phases such as `static_gate`, `semantic_gate`, `test_gate`, and `smoke_gate` cannot persist their own results correctly.

### Root cause

The template mixes two different classes of inputs into one fixed command string:

- static template config:
  script path, `--state-file`, `--closeout-root`
- runtime values:
  `--workflow-id`, `--gate`, `--status`

The runtime values should be provided by the harness workflow controller after each gate run. The current template freezes them too early.

### Deferral reason

This is not being fixed in isolation because upcoming harness work is expected to adjust the manifest/runtime contract around gate execution and backfill orchestration. A narrow patch now would likely be reworked in that follow-up.
