# Validate CLAUDE.local.md

Trace the actual code to verify that CLAUDE.local.md accurately describes the current state of the codebase. Update it where it has drifted.

## Step 1: Read the current CLAUDE.local.md

Read `CLAUDE.local.md` in the repo root. Note every factual claim it makes about code structure, build flow, CLI commands, file locations, and abstractions.

## Step 2: Trace the blueprint build flow

Starting from `dimos/core/blueprints.py`, trace the actual `build()` method step by step:

1. Read `blueprints.py` — find `build()`, follow each method it calls in order
2. Read `module_coordinator.py` — trace `start()`, `deploy_parallel()`, `start_all_modules()`, `loop()`, `stop()`
3. Read `worker.py` / `worker_manager.py` — trace worker pool creation, `deploy_parallel()`, `_worker_loop()`
4. Read `stream.py` — trace `In[T]`/`Out[T]`, `set_transport()`, `subscribe()`, `publish()`
5. Read `transport.py` — verify transport types listed (LCM, SHM, pLCM, ROS, DDS)
6. Read `module.py` — trace `Module.__init__()`, stream instantiation from annotations, RPC setup, `get_skills()`
7. Read `core.py` — verify `@rpc` decorator behavior
8. Read `dimos/agents/annotation.py` — verify `@skill` decorator behavior
9. Read `spec/utils.py` — trace Spec resolution in `_connect_module_refs()`
10. Read `global_config.py` — verify GlobalConfig cascade (defaults → .env → env vars → blueprint → CLI)

For each phase described in CLAUDE.local.md's "Blueprint Build Timeline", confirm:
- Is the ordering still correct?
- Are the method names and file locations accurate?
- Have any new phases been added?
- Have any phases been removed or merged?

## Step 3: Trace the CLI

Read `dimos/robot/cli/dimos.py` and verify:
- All CLI commands listed in CLAUDE.local.md still exist
- No new important commands are missing
- Flag names and descriptions are accurate
- Log file paths are correct

## Step 4: Verify key files table

For each file listed in the "Key Files" table, confirm it still exists and its description is accurate. Check if any important new files should be added (e.g., new core modules, new transport types).

## Step 5: Check abstractions

Verify the core abstractions list is complete and accurate:
- Module, Blueprint, Stream, Transport, Spec — are there new ones?
- Are the one-line descriptions still correct?

## Step 6: Check rules accuracy

Also scan the `.claude/rules/` files for any claims that may have drifted:
- `blueprints.md` — is all_blueprints.py still auto-generated the same way?
- `skills.md` — are the @skill rules still accurate? Any new supported param types?
- `modules.md` — is the stream auto-connection logic still by (name, type)?
- `testing.md` — are the pytest markers and CI scripts still accurate?

## Step 7: Update CLAUDE.local.md

For each discrepancy found:
1. Describe what changed (old → new)
2. Update the relevant section in CLAUDE.local.md
3. If a rule file also needs updating, update it too

Keep the same structure and tone. Don't add bloat — only correct inaccuracies and add genuinely important new information. If something was removed from core, remove it from the docs.

## Step 8: Summary

Present a table of changes made:

```
## CLAUDE.local.md Validation Report

| Section | Status | Change |
|---------|--------|--------|
| Blueprint Build Timeline | Updated | Phase 5 now uses X instead of Y |
| Key Files | Updated | Added new_file.py |
| CLI Reference | OK | No changes needed |
| ...    | ...    | ... |

### Rules updated
- skills.md: added `dict[str, str]` to supported param types
```
