# Fix Doc Discovery Test Isolation

## Problem

`tests/test_doc_discovery.py` requires `src/stogger/_docs/` artifacts
(llms.txt, agent_skill.md) generated only by
`scripts/build_docs_for_package.py`. In parallel tox (`tox -p`),
the `build` env's `shutil.rmtree(_docs)` races with `3.13`/`cov`
test collection, causing FileNotFoundError.

## Fix

Add module-level skip in `tests/test_doc_discovery.py` when
`src/stogger/_docs/` does not exist. Tests still run in
`build`/`outsider` envs where docs are generated.
