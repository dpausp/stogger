# Nix Integration for stogger

Build docs, run tests, develop — all in a Nix shell. Requires Nix with flakes enabled.

## Enable flakes

Add to `~/.config/nix/nix.conf` or `/etc/nix/nix.conf`:

```
experimental-features = nix-command flakes
```

## Development shell

```bash
nix develop
```

Inside the shell, all tools are available:

```bash
build-docs          # build documentation once
live-docs           # start live docs server
pytest              # run tests
ruff check          # lint
ty check src/       # type check
```

With direnv, the shell loads automatically:

```bash
echo "use flake" > .envrc
direnv allow
```

## Build docs

```bash
nix run .#build-docs    # build once
nix run .#live-docs     # live server
```

## Build package and run checks

```bash
nix build               # build the stogger package
nix flake check         # run all checks (tests, linting)
```

## What the flake provides

- Python ≥3.13 with all dependencies
- stogger package built and available
- Documentation tools (Sphinx, Furo, MyST)
- Development tools (pytest, ruff, ty, pre-commit)
