# Phase 0 — Pending Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all pending issues from the previous session — gateway, MiMo, Terax, documentation.

**Architecture:** Direct fixes to existing installations. No new code patterns — just verification and repo documentation.

**Tech Stack:** bash, Python (verify), git

## Global Constraints

- No sudo available — use user-space alternatives only
- WSL2 Ubuntu 22.04 environment
- All changes to ai-workstation-environment must be committed to repo
- Test after every fix before moving to next task

---

### Task 1: Verify ai-workstation gateway fix

**Covers:** [S3.1]

**Files:**
- Verify: `/mnt/d/Projects/ai-workstation/apps/gateway/src/gateway/main.py:10`

**Interfaces:**
- Consumes: PostgreSQL `ai_workstation_gateway` database on port 5433
- Produces: Running gateway on port 8000

- [ ] **Step 1: Verify the fix is in place**

Read `/mnt/d/Projects/ai-workstation/apps/gateway/src/gateway/main.py` line 10.
Expected: `load_dotenv(env_path, override=True)` or similar with `override=True`

- [ ] **Step 2: Start the gateway**

```bash
cd /mnt/d/Projects/ai-workstation
uv run uvicorn gateway.main:app --reload --app-dir apps/gateway/src --port 8000 &
```

- [ ] **Step 3: Verify gateway connects to correct database**

```bash
curl -s http://localhost:8000/health
```
Expected: HTTP 200 with status OK

- [ ] **Step 4: Verify database connectivity**

```bash
curl -s http://localhost:8000/v1/models | head -20
```
Expected: JSON response (not a database error)

- [ ] **Step 5: Commit if any changes needed**

```bash
cd /mnt/d/Projects/ai-workstation
git add -A
git commit -m "fix: verify gateway load_dotenv override fix" || echo "Nothing to commit"
```

---

### Task 2: Swap MiMo binary

**Covers:** [S3.2]

**Files:**
- Modify: `~/.mimocode/bin/mimo` (replace)
- Reference: `~/.local/bin/mimo-new` (source)

**Interfaces:**
- Produces: Active MiMo v0.0.0-main-ec413ad

- [ ] **Step 1: Check current MiMo process**

```bash
ps aux | grep mimo | grep -v grep
```
Expected: Shows PID of running mimo process

- [ ] **Step 2: Gracefully stop the running MiMo**

```bash
# Find and kill the old mimo process
pkill -f "mimo" || true
sleep 2
ps aux | grep mimo | grep -v grep && echo "Still running" || echo "Stopped"
```

- [ ] **Step 3: Verify new binary exists**

```bash
ls -la ~/.local/bin/mimo-new
~/.local/bin/mimo-new --version
```
Expected: v0.0.0-main-ec413ad or similar

- [ ] **Step 4: Swap the binary**

```bash
cp ~/.local/bin/mimo-new ~/.mimocode/bin/mimo
chmod +x ~/.mimocode/bin/mimo
```

- [ ] **Step 5: Verify new binary runs**

```bash
~/.mimocode/bin/mimo --version
```
Expected: Version string matching v0.0.0-main-ec413ad

---

### Task 3: Fix Terax libwebkit2gtk

**Covers:** [S3.3]

**Files:**
- Install: `libwebkit2gtk-4.1-0` system package

**Interfaces:**
- Produces: Functional Terax at `~/.local/bin/terax`

- [ ] **Step 1: Check if Terax launches**

```bash
~/.local/bin/terax --version 2>&1 | head -5
```
Expected: Either version string or error about libwebkit2gtk

- [ ] **Step 2: Try installing via micromamba (user-space)**

```bash
~/.micromamba/bin/micromamba install -y -n base -c conda-forge webkit2gtk 2>&1 || echo "Not in conda-forge"
```

- [ ] **Step 3: If micromamba fails, try downloading the .so directly**

```bash
# Check if available in system package cache
dpkg -l | grep libwebkit2gtk 2>/dev/null || echo "Not installed via dpkg"
apt list --installed 2>/dev/null | grep webkit || echo "Not in apt"
```

- [ ] **Step 4: Try extracting from .deb without dpkg**

```bash
# Download the deb package containing libwebkit2gtk
cd /tmp
apt download libwebkit2gtk-4.1-0 2>&1 || echo "Cannot download (needs sudo)"
```

- [ ] **Step 5: If download succeeds, extract library**

```bash
cd /tmp
ar x libwebkit2gtk-4.1-0_*.deb data.tar.xz 2>/dev/null || ar x libwebkit2gtk-4.1-0_*.deb data.tar.gz
tar xf data.tar.* ./usr/lib/x86_64-linux-gnu/libwebkit2gtk-4.1.so.0 -C ~/.local/lib/ 2>/dev/null || true
export LD_LIBRARY_PATH="$HOME/.local/lib/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
~/.local/bin/terax --version 2>&1 | head -3
```

- [ ] **Step 6: If all fails, document the workaround**

If Terax cannot be fixed without sudo, document in repo that it requires `sudo apt install libwebkit2gtk-4.1-0` and move on.

---

### Task 4: Document fixes in repo

**Covers:** [S3.4]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation-environment/components/zen-browser/component.yaml`
- Create: `/mnt/d/Projects/ai-workstation-environment/components/zen-browser/install.sh`
- Create: `/mnt/d/Projects/ai-workstation-environment/components/zen-browser/check.sh`
- Create: `/mnt/d/Projects/ai-workstation-environment/components/zen-browser/uninstall.sh`
- Modify: `/mnt/d/Projects/ai-workstation-environment/profiles/notebook.yaml` (add zen-browser)
- Create: `~/.bashrc` additions documented as `scripts/wsl2-gui-fix.sh`

**Interfaces:**
- Produces: Repo-documented fixes for Zen Browser, ALSA, LD_LIBRARY_PATH

- [ ] **Step 1: Create Zen Browser component.yaml**

```yaml
name: zen-browser
version: "1.21.9b"
description: "Zen Browser — privacy-focused Firefox fork with AI features"
platforms: [linux]
profiles: [notebook, desktop, host]
depends_on: []
optional: false
packages:
  apt: []
  pacman: []
```

- [ ] **Step 2: Create Zen Browser install.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$HOME/.local/bin"
APPIMAGE_URL="https://github.com/zen-browser/desktop/releases/download/1.21.9b/zen-x86_64.AppImage"
APPIMAGE_PATH="$INSTALL_DIR/zen-browser"
WRAPPER_PATH="$INSTALL_DIR/zen"

echo "Downloading Zen Browser AppImage..."
curl -fsSL "$APPIMAGE_URL" -o "$APPIMAGE_PATH"
chmod +x "$APPIMAGE_PATH"

echo "Creating zen wrapper with LD_LIBRARY_PATH..."
cat > "$WRAPPER_PATH" << 'WRAPPER'
#!/usr/bin/env bash
export LD_LIBRARY_PATH="$HOME/.micromamba/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$HOME/.local/bin/zen-browser" "$@"
WRAPPER
chmod +x "$WRAPPER_PATH"

echo "zen-browser installed: $APPIMAGE_PATH"
echo "zen wrapper created: $WRAPPER_PATH"
```

- [ ] **Step 3: Create Zen Browser check.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail
command -v zen-browser >/dev/null 2>&1 && echo "zen-browser installed" && exit 0
echo "zen-browser not found"
exit 1
```

- [ ] **Step 4: Create Zen Browser uninstall.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail
rm -f "$HOME/.local/bin/zen-browser" "$HOME/.local/bin/zen"
echo "zen-browser removed"
```

- [ ] **Step 5: Add zen-browser to notebook.yaml profile**

Read `/mnt/d/Projects/ai-workstation-environment/profiles/notebook.yaml` and add `zen-bot zen-browser` to the components list.

- [ ] **Step 6: Create WSL2 GUI fix script**

```bash
#!/usr/bin/env bash
set -euo pipefail
# WSL2 GUI Fix — installs ALSA library for GUI apps (Zed, Zen Browser)
# Requires: micromamba installed at ~/.micromamba

echo "Installing alsa-lib via micromamba..."
~/.micromamba/bin/micromamba install -y -n base -c conda-forge alsa-lib

echo "Adding LD_LIBRARY_PATH to .bashrc..."
grep -q 'LD_LIBRARY_PATH.*micromamba/lib' ~/.bashrc || echo '
# WSL2 GUI fix: ALSA library for Zed, Zen Browser, etc.
export LD_LIBRARY_PATH="$HOME/.micromamba/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"' >> ~/.bashrc

echo "Done. Source .bashrc or restart shell."
```

- [ ] **Step 7: Commit all documentation**

```bash
cd /mnt/d/Projects/ai-workstation-environment
git add -A
git commit -m "feat: add zen-browser component and WSL2 GUI fix documentation

- Zen Browser component (AppImage + wrapper with LD_LIBRARY_PATH)
- WSL2 GUI fix script (alsa-lib via micromamba)
- Profile updated to include zen-browser"
```

---

## Self-Review Notes

- All 4 pending items from session addressed
- Each task has verification step
- Repo documentation covers: zen-browser install, ALSA/GUI fix
- Terax fix has fallback if sudo unavailable
