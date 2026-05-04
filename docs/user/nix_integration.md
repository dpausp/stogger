# Nix Integration for stogger

This project includes a comprehensive Nix flake for reproducible development and deployment.

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

### Run stogger CLI directly

```bash
# Run the CLI tool
nix run . -- --help

# Run with arguments
nix run . -- analyze src/
nix run . -- transform --dry-run src/
```

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
# CLI tool is available
stogger --help

# Build documentation
build-docs

# Live documentation server
live-docs

# Run tests
pytest

# Code quality
ruff check
mypy src/

# Development info
stogger-dev
```

### Build Package

```bash
# Build the stogger package
nix build

# Build documentation
nix build .#docs

# Run all checks (tests, linting, docs)
nix flake check
```

## Available Commands

### Apps (nix run)

- nix run . or nix run .#stogger - Run stogger CLI
- nix run .#build-docs - Build documentation
- nix run .#live-docs - Start live documentation server

### Packages (nix build)

- nix build or nix build .#stogger - Build stogger package
- nix build .#docs - Build documentation

### Development

- nix develop - Enter development shell with all dependencies
- nix flake check - Run all checks (build, tests, docs)

## Features

### Complete Development Environment

The Nix flake provides:

- Python with all dependencies
- stogger package built and available
- Documentation tools (Sphinx, Furo, MyST)
- Development tools (pytest, ruff, mypy, pre-commit)
- CLI tools ready to use

### Reproducible Builds

- Pinned dependencies for consistent builds
- Cross-platform support (Linux, macOS, Windows via WSL)
- Isolated environment prevents conflicts

### Easy CI/CD Integration

```yaml
# GitHub Actions example
- name: Setup Nix
  uses: cachix/install-nix-action@v22
  with:
    github_access_token: ${{ secrets.GITHUB_TOKEN }}

- name: Run checks
  run: nix flake check

- name: Build documentation
  run: nix build .#docs
```

## Directory Structure

```
.
├── flake.nix          # Nix flake definition
├── flake.lock         # Locked dependencies
├── .envrc             # direnv configuration
├── docs/user_guide/nix_integration.md  # This file
└── ...
```

## Customization

### Adding Dependencies

Edit flake.nix and add to the appropriate section:

```nix
pythonEnv = pkgs.python311.withPackages (ps: with ps; [
  # Add new dependencies here
  your-new-package
]);
```

### Custom Scripts

Add new scripts in the outputs section:

```nix
myScript = pkgs.writeShellScriptBin "my-script" ''
  echo "Custom script"
'';
```

## Troubleshooting

### Flake not found

```bash
# Update flake inputs
nix flake update

# Clear cache
nix store gc
```

### Permission issues

```bash
# Fix permissions
sudo chown -R $USER:$USER ~/.cache/nix
```

### Python path issues

The development shell automatically sets up PYTHONPATH to include the built stogger package.

### Documentation build fails

```bash
# Clean and rebuild
nix run .#build-docs
```

## Integration with Other Tools

### VS Code

Install the Nix IDE extension and use:

```json
{
    "nix.enableLanguageServer": true,
    "nix.serverPath": "nil"
}
```

### direnv

Automatic environment loading:

```bash
# One-time setup
echo "use flake" > .envrc
direnv allow

# Environment loads automatically when entering directory
cd stogger  # Environment activates
cd ..         # Environment deactivates
```

### Docker

Build a Docker image with Nix:

```bash
# Create Docker image
nix build .#dockerImage

# Load and run
docker load < result
docker run stogger:latest stogger --help
```

## Performance Tips

### Binary Cache

Use the official Nix binary cache:

```bash
# Add to nix.conf
substituters = https://cache.nixos.org/
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
```

### Parallel Builds

```bash
# Use multiple cores
nix build --max-jobs auto
```

## Examples

### Development Workflow

```bash
# Clone and enter
git clone <repo>
cd stogger

# Automatic environment (with direnv)
# Or manual: nix develop

# Work on code
vim src/stogger/core.py

# Test changes
pytest tests/

# Build documentation
build-docs

# Run CLI
stoggertools migrate src/
```

### CI/CD Pipeline

```bash
# Check everything
nix flake check

# Build for deployment
nix build

# Create deployment artifact
nix bundle .#stogger
```

The Nix integration provides a complete, reproducible development and deployment environment for stogger!