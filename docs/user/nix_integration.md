# Nix Integration for stogger

This project includes a Nix flake for reproducible development environments.

## Quick Start

### Prerequisites

- Nix with flakes enabled
- Optional: direnv for automatic environment loading

### Enable Nix Flakes

Add to your ~/.config/nix/nix.conf or /etc/nix/nix.conf:
```
experimental-features = nix-command flakes
```

## Usage

### Build Documentation

```bash
# Build documentation once
nix run .#build-docs

# Start live documentation server
nix run .#live-docs
```

### Development Environment

```bash
# Enter development shell
nix develop

# Or with direnv (automatic)
echo "use flake" > .envrc
direnv allow
```

Inside the development shell:
```bash
# Build documentation
build-docs

# Live documentation server
live-docs

# Run tests
pytest

# Code quality
ruff check
ty check src/
```

### Build Package

```bash
# Build the stogger package
nix build

# Run all checks (tests, linting)
nix flake check
```

## Features

### Complete Development Environment

The Nix flake provides:

- Python ≥3.13 with all dependencies
- stogger package built and available
- Documentation tools (Sphinx, Furo, MyST)
- Development tools (pytest, ruff, ty, pre-commit)


