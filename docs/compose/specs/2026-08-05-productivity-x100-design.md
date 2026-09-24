# Productivity x100 — Design Spec

> Generated from brainstorming session 2026-08-05. Defines the architecture for
> pending fixes + 3 new features that multiply development productivity.

---

## [S1] Problem

The current AI workstation setup has gaps:
- Gateway fix unverified (load_dotenv override applied but not tested)
- MiMo binary not swapped (running old version)
- Terax broken (missing libwebkit2gtk)
- All fixes undocumented in repo

Beyond fixes, the existing tools (Claude Code, MiMo, Zed, n8n, ai-workstation gateway) operate in isolation. Every session starts from zero context. Development loops require manual handoffs between planning, coding, testing, and PR creation.

---

## [S2] Solution Overview

Three layered features on top of the existing infrastructure:

1. **Context Engine 2.0** — Indexes all projects into Qdrant, injects relevant context into every query transparently
2. **Autonomous Dev Loop** — Full autonomous pipeline: feature request → plan → implement → test → PR → Telegram notification
3. **Unified Command Center** — Hybrid CLI + web dashboard as single entrypoint for all agents, tasks, and monitoring

Plus a **Phase 0** for pending fixes (prerequisites).

---

## [S3] Phase 0 — Pending Fixes

### [S3.1] Gateway load_dotenv fix verification
- Restart ai-workstation gateway to verify `load_dotenv(override=True)` resolves the database connection issue
- Verify it connects to `ai_workstation_gateway` database correctly

### [S3.2] MiMo binary swap
- Stop running MiMo process (PID varies)
- Replace `~/.mimocode/bin/mimo` with `~/.local/bin/mimo-new`
- Verify new version runs

### [S3.3] Terax libwebkit2gtk fix
- Install `libwebkit2gtk-4.1-0` (via sudo if available, or find user-space alternative)
- Verify Terax launches

### [S3.4] Documentation in repo
- Add Zen Browser component to ai-workstation-environment
- Document ALSA fix and LD_LIBRARY_PATH
- Add wrapper scripts to components

---

## [S4] Context Engine 2.0

### [S4.1] Scope
- **Index all projects** in `/mnt/d/Projects/` automatically
- **File watcher** for real-time updates (inotify/fswatch)
- **Content types**: code + docs + conversations + decisions + Telegram/notes

### [S4.2] Architecture — Gateway Plugin
- Implement as middleware/extension of the ai-workstation gateway
- Intercepts every `/v1/chat/completions` request
- Enriches `messages` with relevant context before passing to the pipeline
- Uses existing Qdrant infrastructure with **per-project namespaces**

### [S4.3] Namespace Isolation
- Each project gets its own Qdrant collection: `ctx_<project_slug>`
- Searches are scoped to the active project namespace
- Cross-project search available via explicit override (`--all-projects` or `@all`)

### [S4.4] Embeddings
- Replace current MD5 placeholder with real embeddings model
- Options: `sentence-transformers` local (recommended for privacy) or OpenAI `text-embedding-3-small`
- Store embeddings alongside metadata (file path, timestamp, project, content type)

### [S4.5] File Watcher
- Watch configured project directories for changes (create/update/delete)
- Debounce rapid changes (5s window)
- Re-index changed files incrementally

### [S4.6] API Endpoints
- `POST /v1/context/index` — Trigger indexing (full or incremental)
- `GET /v1/context/status` — Index status per project
- `POST /v1/context/search` — Direct context search (for debugging/tools)
- `DELETE /v1/context/<project>` — Remove project from index

---

## [S5] Autonomous Dev Loop

### [S5.1] Scope
- Full autonomous: feature request → plan → implement → test → PR → Telegram notification
- Human touch point: PR review (everything before is automatic)

### [S5.2] Architecture
- Extends the existing `auto_orchestrator` component from ai-workstation-environment
- Integrates with ai-workstation gateway as the execution backend
- Uses existing AI Proxy (port 8090) for model routing
- Dual-model strategy: Claude/Gemini for planning and review, local Ollama (qwen2.5-coder) for execution

### [S5.3] Pipeline Stages
1. **Receive** — Task arrives via Command Center, Telegram, or API
2. **Decompose** — Break feature into sub-tasks (reuse existing `decomposer.py`)
3. **Assign** — Route each sub-task to appropriate model/agent (reuse `assigner.py`)
4. **Execute** — Run sub-tasks via gateway (code generation, file edits, shell commands)
5. **Test** — Run project tests, linting, type checking
6. **Iterate** — If tests fail, debug and re-execute (max 3 retries)
7. **PR** — Create GitHub PR with description, linked issues
8. **Notify** — Telegram notification with PR link + summary

### [S5.4] State Machine
```
RECEIVED → DECOMPOSING → PLANNING → EXECUTING → TESTING → PR_CREATING → NOTIFYING → DONE
                        ↑__________↓ (retry loop on test failure)
```

### [S5.5] Telegram Integration
- Reuse existing Telegram bot component
- Send notifications at: start, stage transitions, errors, completion
- Support basic commands: `/status`, `/abort`, `/pause`

---

## [S6] Unified Command Center

### [S6.1] Scope
- Hybrid: CLI for quick actions + web dashboard for monitoring/management
- Single entrypoint for all AI workstation features

### [S6.2] CLI (`aw` command)
- `aw task "implement feature X"` — Launch autonomous dev loop
- `aw status` — Show running tasks and agents
- `aw context status` — Show index status across projects
- `aw models` — List available models, costs, current routing
- `aw logs <task-id>` — Stream logs for a running task

### [S6.3] Web Dashboard
- Real-time task monitoring (WebSocket for live updates)
- Agent status and history
- Model usage and cost analytics
- Context engine index browser
- Configuration panel (models, routing, projects to index)

### [S6.4] Architecture
- Backend: FastAPI (extend ai-workstation gateway)
- Frontend: Lightweight React/Vue SPA or server-rendered templates
- Communication: REST + WebSocket
- Auth: Reuse existing API key middleware

---

## [S7] Technical Constraints

- Python 3.11+ for new packages (match existing ai-workstation)
- Async-first (match existing patterns)
- Qdrant for vector storage (reuse existing infrastructure)
- Telegram Bot API for notifications
- GitHub API (via PyGithub) for PR creation
- File watching: `watchdog` library
- Embeddings: `sentence-transformers` (local, no API key needed)
- CLI: `typer` (match existing CLI framework)

---

## [S8] Dependencies Between Features

```
Phase 0 (fixes) ─┐
                 ├──► Context Engine 2.0 ──► Autonomous Dev Loop ──► Command Center
                 │         (provides context      (provides tasks      (provides UX
                 │          for planning)          for monitoring)      for everything)
                 │
                 └──► Command Center (can be built in parallel with Context Engine)
```

Context Engine and Command Center can be developed in parallel. Autonomous Dev Loop depends on Context Engine for intelligent planning.

---

## [S9] Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Gateway operational | Fix unverified | Running, verified |
| MiMo version | Old (busy process) | New binary active |
| Terax functional | Broken | Launching |
| Context injection | None | Every query enriched |
| Index coverage | 0 projects | All /mnt/d/Projects/ |
| Dev loop autonomy | 0% | Full (request → PR) |
| Entrypoints | 5+ tools | 1 unified interface |
