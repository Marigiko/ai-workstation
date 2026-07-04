# ADR-001: Monorepo Structure with uv Workspaces

## Status
Accepted

## Context
Need to organize a multi-package Python project for the AI Workstation platform.
Options considered:
1. Single package with modules
2. Monorepo with separate repos
3. Monorepo with uv workspaces
4. Monorepo with poetry workspaces

## Decision
Use uv workspaces for monorepo management.

## Rationale
- uv is faster than poetry (Rust-based)
- Native workspace support with proper dependency resolution
- Single source of truth for dependencies
- Atomic commits across packages
- Shared CI/CD configuration
- Easier to maintain than separate repos for a single developer/team

## Consequences
- All packages share the same virtual environment
- Dependencies must be compatible across packages
- Need to manage workspace sources in each package's pyproject.toml
