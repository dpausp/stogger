# Agent Guidelines

## Before Committing

Run `CI=1 uv run tox -p` (which includes `docs` in `env_list`) before every commit. This ensures
generated API documentation in `docs/api/` stays in sync with docstrings. The `docs`
tox environment regenerates autoapi RST files from source — committing without a prior
docs build leaves stale generated files that show up as dirty on the next build.
