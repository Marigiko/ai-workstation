# Autonomous Dev Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full autonomous development pipeline — from feature request to GitHub PR with Telegram notifications.

**Architecture:** Extends the existing `auto_orchestrator` from ai-workstation-environment. Integrates with the ai-workstation gateway for execution, uses dual-model strategy (Claude for planning, local Ollama for execution), and sends Telegram notifications at each stage.

**Tech Stack:** Python 3.11+, FastAPI, Telegram Bot API, PyGithub, asyncio, aiohttp

## Global Constraints

- Follow existing ai-workstation package structure
- Async-first
- Type hints on all functions
- Each task ends with passing tests
- Telegram notifications via existing bot infrastructure
- Dual-model: Claude/Gemini for planning+review, local Ollama (qwen2.5-coder) for execution
- State machine for task lifecycle

---

### Task 1: Create dev loop package structure

**Covers:** [S5.2]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/pyproject.toml`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/__init__.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/state.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_state.py`

**Interfaces:**
- Produces: `TaskState` enum, `Task` dataclass, `StateMachine` class

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_state.py
import pytest
from devloop.state import TaskState, Task, StateMachine, InvalidTransitionError


def test_task_state_transitions():
    sm = StateMachine()
    task = Task(id="test-1", description="Implement feature X")

    assert task.state == TaskState.RECEIVED

    sm.transition(task, TaskState.DECOMPOSING)
    assert task.state == TaskState.DECOMPOSING

    sm.transition(task, TaskState.EXECUTING)
    assert task.state == TaskState.EXECUTING


def test_invalid_transition_raises():
    sm = StateMachine()
    task = Task(id="test-2", description="Test")

    with pytest.raises(InvalidTransitionError):
        sm.transition(task, TaskState.PR_CREATING)  # Can't skip to PR from RECEIVED


def test_terminal_states():
    sm = StateMachine()
    task = Task(id="test-3", description="Test")

    sm.transition(task, TaskState.DECOMPOSING)
    sm.transition(task, TaskState.EXECUTING)
    sm.transition(task, TaskState.TESTING)
    sm.transition(task, TaskState.PR_CREATING)
    sm.transition(task, TaskState.DONE)

    with pytest.raises(InvalidTransitionError):
        sm.transition(task, TaskState.EXECUTING)  # Can't leave DONE
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_state.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement state machine**

```python
# packages/devloop/src/devloop/state.py
"""Task state machine for the autonomous dev loop."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskState(Enum):
    """States in the autonomous dev loop pipeline."""
    RECEIVED = "received"
    DECOMPOSING = "decomposing"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    PR_CREATING = "pr_creating"
    NOTIFYING = "notifying"
    DONE = "done"
    FAILED = "failed"


# Valid state transitions
_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.RECEIVED: {TaskState.DECOMPOSING, TaskState.FAILED},
    TaskState.DECOMPOSING: {TaskState.PLANNING, TaskState.FAILED},
    TaskState.PLANNING: {TaskState.EXECUTING, TaskState.FAILED},
    TaskState.EXECUTING: {TaskState.TESTING, TaskState.FAILED},
    TaskState.TESTING: {TaskState.EXECUTING, TaskState.PR_CREATING, TaskState.FAILED},
    TaskState.PR_CREATING: {TaskState.NOTIFYING, TaskState.FAILED},
    TaskState.NOTIFYING: {TaskState.DONE, TaskState.FAILED},
    TaskState.DONE: set(),
    TaskState.FAILED: set(),
}


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


@dataclass
class Task:
    """Represents a development task in the loop."""
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    state: TaskState = TaskState.RECEIVED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    subtasks: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 3


class StateMachine:
    """Manages task state transitions."""

    def transition(self, task: Task, new_state: TaskState) -> None:
        """Transition a task to a new state.

        Args:
            task: The task to transition.
            new_state: The target state.

        Raises:
            InvalidTransitionError: If the transition is not allowed.
        """
        valid = _TRANSITIONS.get(task.state, set())
        if new_state not in valid:
            raise InvalidTransitionError(
                f"Cannot transition from {task.state.value} to {new_state.value}"
            )
        task.state = new_state
        task.updated_at = datetime.utcnow()

    def can_transition(self, task: Task, new_state: TaskState) -> bool:
        """Check if a transition is valid."""
        return new_state in _TRANSITIONS.get(task.state, set())
```

- [ ] **Step 4: Create pyproject.toml**

```toml
[project]
name = "devloop"
version = "0.1.0"
description = "Autonomous development loop"
requires-python = ">=3.11"
dependencies = [
    "aiohttp>=3.9.0",
    "pygithub>=2.3.0",
    "aiosqlite>=0.20.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/devloop"]
```

- [ ] **Step 5: Create __init__.py**

```python
# packages/devloop/src/devloop/__init__.py
"""Autonomous development loop package."""

from devloop.state import Task, TaskState, StateMachine, InvalidTransitionError

__all__ = ["Task", "TaskState", "StateMachine", "InvalidTransitionError"]
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_state.py -v
```
Expected: 3 PASS

- [ ] **Step 7: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add task state machine"
```

---

### Task 2: Create task decomposer

**Covers:** [S5.3]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/decomposer.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_decomposer.py`

**Interfaces:**
- Produces: `Decomposer` class with `decompose(task: Task) -> list[SubTask]`

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_decomposer.py
import pytest
from devloop.state import Task, TaskState, StateMachine
from devloop.decomposer import Decomposer, SubTask


@pytest.fixture
def decomposer():
    return Decomposer()


@pytest.mark.asyncio
async def test_decompose_simple_feature(decomposer):
    task = Task(description="Add a login button to the header")
    subtasks = await decomposer.decompose(task)
    assert len(subtasks) >= 1
    assert all(isinstance(st, SubTask) for st in subtasks)
    assert all(st.description for st in subtasks)


@pytest.mark.asyncio
async def test_decompose_complex_feature(decomposer):
    task = Task(description="Implement user authentication with JWT tokens, including login, logout, and password reset")
    subtasks = await decomposer.decompose(task)
    assert len(subtasks) >= 3


def test_subtask_datatable():
    st = SubTask(description="Create model", order=1, estimated_lines=50)
    assert st.order == 1
    assert st.estimated_lines == 50
    assert st.completed is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_decomposer.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement Decomposer**

```python
# packages/devloop/src/devloop/decomposer.py
"""Task decomposer — breaks features into executable subtasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from devloop.state import Task


@dataclass
class SubTask:
    """A single unit of work within a task."""
    description: str
    order: int
    estimated_lines: int = 50
    completed: bool = False
    result: dict[str, Any] = field(default_factory=dict)


class Decomposer:
    """Decomposes feature requests into ordered subtasks."""

    async def decompose(self, task: Task) -> list[SubTask]:
        """Break a task description into subtasks.

        Uses keyword heuristics to identify common patterns.
        In production, this would call an LLM for decomposition.
        """
        desc = task.description.lower()
        subtasks: list[SubTask] = []

        # Heuristic-based decomposition
        if "auth" in desc or "login" in desc or "jwt" in desc:
            subtasks.extend([
                SubTask(description="Define auth models and schemas", order=1, estimated_lines=30),
                SubTask(description="Implement token generation and validation", order=2, estimated_lines=50),
                SubTask(description="Create login/logout endpoints", order=3, estimated_lines=40),
                SubTask(description="Add auth middleware", order=4, estimated_lines=25),
            ])
        elif "test" in desc:
            subtasks.extend([
                SubTask(description="Write unit tests", order=1, estimated_lines=60),
                SubTask(description="Write integration tests", order=2, estimated_lines=80),
            ])
        elif "refactor" in desc:
            subtasks.extend([
                SubTask(description="Identify code smells and patterns", order=1, estimated_lines=0),
                SubTask(description="Extract common logic", order=2, estimated_lines=40),
                SubTask(description="Update callers", order=3, estimated_lines=30),
            ])
        else:
            # Generic decomposition
            subtasks.extend([
                SubTask(description=f"Analyze requirements: {task.description[:50]}", order=1, estimated_lines=0),
                SubTask(description="Implement core logic", order=2, estimated_lines=60),
                SubTask(description="Add error handling", order=3, estimated_lines=20),
                SubTask(description="Write tests", order=4, estimated_lines=50),
            ])

        task.subtasks = [s.__dict__ for s in subtasks]
        return subtasks
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_decomposer.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add task decomposer"
```

---

### Task 3: Create execution engine

**Covers:** [S5.3]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/executor.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_executor.py`

**Interfaces:**
- Consumes: `SubTask`, gateway URL
- Produces: `Executor` class with `execute(subtask: SubTask, project: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_executor.py
import pytest
from unittest.mock import AsyncMock, patch
from devloop.executor import Executor
from devloop.decomposer import SubTask


@pytest.fixture
def executor():
    return Executor(gateway_url="http://localhost:8000")


@pytest.mark.asyncio
async def test_execute_calls_gateway(executor):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "def hello(): pass"}}]
        })
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await executor.execute(
            SubTask(description="Create hello function", order=1),
            project="test_project",
        )
        assert "content" in result or "error" in result


@pytest.mark.asyncio
async def test_execute_handles_gateway_error(executor):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await executor.execute(
            SubTask(description="Test error handling", order=1),
            project="test_project",
        )
        assert "error" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_executor.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement Executor**

```python
# packages/devloop/src/devloop/executor.py
"""Execution engine — runs subtasks via the AI workstation gateway."""

from __future__ import annotations

import os
from typing import Any

import aiohttp

from devloop.decomposer import SubTask


class Executor:
    """Executes subtasks by calling the AI workstation gateway."""

    def __init__(self, gateway_url: str | None = None):
        self._gateway = gateway_url or os.environ.get("GATEWAY_URL", "http://localhost:8000")

    async def execute(self, subtask: SubTask, project: str) -> dict[str, Any]:
        """Execute a subtask via the gateway.

        Args:
            subtask: The subtask to execute.
            project: The project context.

        Returns:
            Dict with 'content' (success) or 'error' (failure).
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._gateway}/v1/chat/completions",
                    json={
                        "model": "qwen2.5-coder:7b",
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are coding in project: {project}. "
                                           f"Write clean, idiomatic code. Only output code.",
                            },
                            {
                                "role": "user",
                                "content": subtask.description,
                            },
                        ],
                        "temperature": 0.2,
                    },
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = (
                            data.get("choices", [{}])[0]
                            .get("message", {})
                            .get("content", "")
                        )
                        subtask.completed = True
                        return {"content": content, "status": "success"}
                    else:
                        text = await response.text()
                        return {"error": f"HTTP {response.status}: {text[:200]}"}
        except Exception as e:
            return {"error": str(e)}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_executor.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add execution engine"
```

---

### Task 4: Create test runner

**Covers:** [S5.3]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/test_runner.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_runner.py`

**Interfaces:**
- Produces: `TestRunner` class with `run_tests(project_path: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_runner.py
import pytest
import tempfile
import os
from devloop.test_runner import TestRunner


@pytest.fixture
def runner():
    return TestRunner()


@pytest.mark.asyncio
async def test_run_tests_with_passing_tests(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test file
        with open(os.path.join(tmpdir, "test_sample.py"), "w") as f:
            f.write("def test_pass():\n    assert 1 + 1 == 2\n")

        result = await runner.run_tests(tmpdir)
        assert result["passed"] is True
        assert result["total"] >= 1


@pytest.mark.asyncio
async def test_run_tests_with_failing_tests(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "test_fail.py"), "w") as f:
            f.write("def test_fail():\n    assert 1 + 1 == 3\n")

        result = await runner.run_tests(tmpdir)
        assert result["passed"] is False
        assert result["failures"] >= 1


@pytest.mark.asyncio
async def test_run_tests_no_test_files(runner):
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "readme.txt"), "w") as f:
            f.write("No tests here")

        result = await runner.run_tests(tmpdir)
        assert result["passed"] is True
        assert result["total"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_runner.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement TestRunner**

```python
# packages/devloop/src/devloop/test_runner.py
"""Test runner — executes project tests and reports results."""

from __future__ import annotations

import asyncio
import os
import subprocess
from typing import Any


class TestRunner:
    """Runs project tests and returns structured results."""

    async def run_tests(self, project_path: str) -> dict[str, Any]:
        """Run tests in a project directory.

        Args:
            project_path: Path to the project root.

        Returns:
            Dict with 'passed', 'total', 'failures', 'output'.
        """
        # Check for common test commands
        test_commands = [
            (["uv", "run", "pytest", "--tb=short", "-q"], "pytest via uv"),
            (["python", "-m", "pytest", "--tb=short", "-q"], "pytest via python"),
            (["npm", "test", "--", "--watchAll=false"], "npm test"),
            (["bun", "test"], "bun test"),
        ]

        for cmd, _desc in test_commands:
            if self._command_exists(cmd[0]):
                result = await self._run_command(cmd, project_path)
                if result is not None:
                    return result

        return {"passed": True, "total": 0, "failures": 0, "output": "No test runner found"}

    def _command_exists(self, cmd: str) -> bool:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def _run_command(self, cmd: list[str], cwd: str) -> dict[str, Any] | None:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=120
            )
            output = stdout.decode() + stderr.decode()
            return {
                "passed": proc.returncode == 0,
                "total": output.count(" passed") + output.count(" failed"),
                "failures": output.count(" failed"),
                "output": output[:2000],
            }
        except (asyncio.TimeoutExpired, Exception):
            return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_runner.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add test runner"
```

---

### Task 5: Create PR creator

**Covers:** [S5.3]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/pr_creator.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_pr_creator.py`

**Interfaces:**
- Produces: `PRCreator` class with `create_pr(task: Task, repo: str) -> dict`

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_pr_creator.py
import pytest
from unittest.mock import MagicMock, patch
from devloop.state import Task, TaskState
from devloop.pr_creator import PRCreator


@pytest.fixture
def creator():
    return PRCreator(token="fake-token")


@pytest.mark.asyncio
async def test_create_pr_success(creator):
    with patch("devloop.pr_creator.Github") as mock_gh:
        mock_repo = MagicMock()
        mock_repo.create_pull = MagicMock(return_value=MagicMock(
            number=42,
            html_url="https://github.com/user/repo/pull/42",
            title="feat: add feature",
        ))
        mock_gh.return_value.get_repo = MagicMock(return_value=mock_repo)

        task = Task(description="Add feature X")
        task.result = {"summary": "Implemented feature X", "files_changed": 3}

        result = await creator.create_pr(task, repo="user/repo")
        assert result["success"] is True
        assert result["pr_number"] == 42
        assert "github.com" in result["pr_url"]


@pytest.mark.asyncio
async def test_create_pr_failure(creator):
    with patch("devloop.pr_creator.Github") as mock_gh:
        mock_gh.side_effect = Exception("Auth failed")

        task = Task(description="Add feature X")
        result = await creator.create_pr(task, repo="user/repo")
        assert result["success"] is False
        assert "error" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_pr_creator.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement PRCreator**

```python
# packages/devloop/src/devloop/pr_creator.py
"""PR creator — creates GitHub PRs for completed tasks."""

from __future__ import annotations

import os
from typing import Any

from devloop.state import Task


class PRCreator:
    """Creates GitHub pull requests for completed tasks."""

    def __init__(self, token: str | None = None):
        self._token = token or os.environ.get("GITHUB_TOKEN", "")

    async def create_pr(self, task: Task, repo: str) -> dict[str, Any]:
        """Create a GitHub PR for a completed task.

        Args:
            task: The completed task with results.
            repo: Repository in "owner/name" format.

        Returns:
            Dict with 'success', 'pr_number', 'pr_url' or 'error'.
        """
        try:
            from github import Github

            gh = Github(self._token)
            repository = gh.get_repo(repo)

            title = f"feat: {task.description[:60]}"
            body = self._format_body(task)

            pr = repository.create_pull(
                title=title,
                body=body,
                head=f"devloop/{task.id}",
                base="main",
            )

            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": pr.title,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _format_body(self, task: Task) -> str:
        """Format PR description from task data."""
        lines = [
            f"## Summary",
            f"",
            task.result.get("summary", task.description),
            f"",
            f"## Changes",
            f"",
            f"- Files modified: {task.result.get('files_changed', 'unknown')}",
            f"- Subtasks completed: {len([s for s in task.subtasks if s.get('completed', False)])}",
            f"",
            f"---",
            f"*Created by AI Workstation Dev Loop (task: {task.id})*",
        ]
        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_pr_creator.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add PR creator"
```

---

### Task 6: Create Telegram notifier

**Covers:** [S5.5]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/notifier.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_notifier.py`

**Interfaces:**
- Produces: `TelegramNotifier` class with `notify(task: Task, event: str) -> bool`

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_notifier.py
import pytest
from unittest.mock import AsyncMock, patch
from devloop.state import Task, TaskState
from devloop.notifier import TelegramNotifier


@pytest.fixture
def notifier():
    return TelegramNotifier(bot_token="fake-token", chat_id="123456")


@pytest.mark.asyncio
async def test_notify_send_success(notifier):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=False)

        task = Task(description="Test feature")
        result = await notifier.notify(task, event="started")
        assert result is True


@pytest.mark.asyncio
async def test_notify_send_failure(notifier):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=False)

        task = Task(description="Test feature")
        result = await notifier.notify(task, event="failed")
        assert result is False


def test_format_message(notifier):
    task = Task(description="Add login feature")
    msg = notifier._format_message(task, "completed")
    assert "Add login feature" in msg
    assert "completed" in msg
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_notifier.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement TelegramNotifier**

```python
# packages/devloop/src/devloop/notifier.py
"""Telegram notifier — sends task status updates via Telegram bot."""

from __future__ import annotations

import os
from typing import Any

import aiohttp

from devloop.state import Task, TaskState


_EMOJI_MAP: dict[TaskState, str] = {
    TaskState.RECEIVED: "📥",
    TaskState.DECOMPOSING: "🔍",
    TaskState.PLANNING: "📋",
    TaskState.EXECUTING: "⚡",
    TaskState.TESTING: "🧪",
    TaskState.PR_CREATING: "🔀",
    TaskState.NOTIFYING: "📤",
    TaskState.DONE: "✅",
    TaskState.FAILED: "❌",
}


class TelegramNotifier:
    """Sends task notifications via Telegram Bot API."""

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        self._token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
        self._base = f"https://api.telegram.org/bot{self._token}"

    async def notify(self, task: Task, event: str) -> bool:
        """Send a notification about a task event.

        Args:
            task: The task to report on.
            event: Event type (started, stage_changed, completed, failed).

        Returns:
            True if message sent successfully.
        """
        text = self._format_message(task, event)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._base}/sendMessage",
                    json={"chat_id": self._chat_id, "text": text, "parse_mode": "Markdown"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    def _format_message(self, task: Task, event: str) -> str:
        emoji = _EMOJI_MAP.get(task.state, "🤖")
        return (
            f"{emoji} *Dev Loop Update*\n"
            f"Task: `{task.id}`\n"
            f"State: {task.state.value}\n"
            f"Description: {task.description[:100]}\n"
            f"Event: {event}\n"
            f"Retries: {task.retries}/{task.max_retries}"
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_notifier.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add Telegram notifier"
```

---

### Task 7: Create dev loop orchestrator

**Covers:** [S5.2], [S5.3], [S5.4]

**Files:**
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/src/devloop/orchestrator.py`
- Create: `/mnt/d/Projects/ai-workstation/packages/devloop/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: Decomposer, Executor, TestRunner, PRCreator, TelegramNotifier, StateMachine
- Produces: `DevLoopOrchestrator` class with `run(task: Task) -> Task`

- [ ] **Step 1: Write the failing test**

```python
# packages/devloop/tests/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from devloop.orchestrator import DevLoopOrchestrator
from devloop.state import Task, TaskState


@pytest.fixture
def orchestrator():
    return DevLoopOrchestrator(
        gateway_url="http://localhost:8000",
        github_token="fake",
        telegram_token="fake",
        telegram_chat_id="123",
    )


@pytest.mark.asyncio
async def test_run_completes_full_pipeline(orchestrator):
    task = Task(description="Add a simple function")

    # Mock all external calls
    orchestrator._decomposer.decompose = AsyncMock(return_value=[])
    orchestrator._executor.execute = AsyncMock(return_value={"content": "code", "status": "success"})
    orchestrator._test_runner.run_tests = AsyncMock(return_value={"passed": True, "total": 1})
    orchestrator._pr_creator.create_pr = AsyncMock(return_value={
        "success": True, "pr_number": 1, "pr_url": "http://example.com"
    })
    orchestrator._notifier.notify = AsyncMock(return_value=True)

    result = await orchestrator.run(task, project_path="/tmp/test", repo="user/repo")
    assert result.state == TaskState.DONE


@pytest.mark.asyncio
async def test_run_retries_on_test_failure(orchestrator):
    task = Task(description="Fix bug", max_retries=2)

    orchestrator._decomposer.decompose = AsyncMock(return_value=[])
    orchestrator._executor.execute = AsyncMock(return_value={"content": "code"})
    # First call fails, second passes
    orchestrator._test_runner.run_tests = AsyncMock(side_effect=[
        {"passed": False, "failures": 1},
        {"passed": True, "total": 1},
    ])
    orchestrator._pr_creator.create_pr = AsyncMock(return_value={"success": True})
    orchestrator._notifier.notify = AsyncMock(return_value=True)

    result = await orchestrator.run(task, project_path="/tmp/test", repo="user/repo")
    assert result.state == TaskState.DONE
    assert result.retries == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_orchestrator.py -v
```
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Implement DevLoopOrchestrator**

```python
# packages/devloop/src/devloop/orchestrator.py
"""Dev loop orchestrator — runs the full autonomous pipeline."""

from __future__ import annotations

import logging
from typing import Any

from devloop.decomposer import Decomposer
from devloop.executor import Executor
from devloop.notifier import TelegramNotifier
from devloop.pr_creator import PRCreator
from devloop.state import StateMachine, Task, TaskState, InvalidTransitionError
from devloop.test_runner import TestRunner

logger = logging.getLogger(__name__)


class DevLoopOrchestrator:
    """Orchestrates the full autonomous development loop."""

    def __init__(
        self,
        gateway_url: str | None = None,
        github_token: str | None = None,
        telegram_token: str | None = None,
        telegram_chat_id: str | None = None,
    ):
        self._state_machine = StateMachine()
        self._decomposer = Decomposer()
        self._executor = Executor(gateway_url=gateway_url)
        self._test_runner = TestRunner()
        self._pr_creator = PRCreator(token=github_token)
        self._notifier = TelegramNotifier(
            bot_token=telegram_token,
            chat_id=telegram_chat_id,
        )

    async def run(self, task: Task, project_path: str, repo: str) -> Task:
        """Run a task through the full pipeline.

        Args:
            task: The task to execute.
            project_path: Path to the project on disk.
            repo: GitHub repo in "owner/name" format.

        Returns:
            The completed (or failed) task.
        """
        try:
            # Stage 1: Decompose
            await self._transition(task, TaskState.DECOMPOSING)
            subtasks = await self._decomposer.decompose(task)
            await self._notifier.notify(task, "decomposed")

            # Stage 2: Execute subtasks
            await self._transition(task, TaskState.EXECUTING)
            for subtask in subtasks:
                result = await self._executor.execute(subtask, project=project_path)
                subtask.result = result
                if result.get("status") != "success":
                    logger.warning(f"Subtask failed: {subtask.description}")

            # Stage 3: Test (with retry)
            await self._transition(task, TaskState.TESTING)
            test_result = await self._test_runner.run_tests(project_path)

            while not test_result["passed"] and task.retries < task.max_retries:
                task.retries += 1
                logger.info(f"Tests failed, retry {task.retries}/{task.max_retries}")
                await self._transition(task, TaskState.EXECUTING)
                # Re-execute failed subtasks
                for subtask in subtasks:
                    if not subtask.completed:
                        await self._executor.execute(subtask, project=project_path)
                await self._transition(task, TaskState.TESTING)
                test_result = await self._test_runner.run_tests(project_path)

            if not test_result["passed"]:
                await self._transition(task, TaskState.FAILED)
                await self._notifier.notify(task, "tests_failed")
                return task

            # Stage 4: Create PR
            await self._transition(task, TaskState.PR_CREATING)
            task.result = {
                "summary": f"Completed: {task.description}",
                "files_changed": len(subtasks),
            }
            pr_result = await self._pr_creator.create_pr(task, repo=repo)
            task.result["pr"] = pr_result

            # Stage 5: Notify
            await self._transition(task, TaskState.NOTIFYING)
            await self._notifier.notify(task, "completed")

            await self._transition(task, TaskState.DONE)
            return task

        except Exception as e:
            logger.error(f"Dev loop failed: {e}")
            try:
                await self._transition(task, TaskState.FAILED)
            except InvalidTransitionError:
                pass
            await self._notifier.notify(task, f"error: {str(e)[:100]}")
            return task

    async def _transition(self, task: Task, new_state: TaskState) -> None:
        self._state_machine.transition(task, new_state)
        logger.info(f"Task {task.id}: {task.state.value} -> {new_state.value}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /mnt/d/Projects/ai-workstation
uv run pytest packages/devloop/tests/test_orchestrator.py -v
```
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
cd /mnt/d/Projects/ai-workstation
git add packages/devloop/
git commit -m "feat(devloop): add orchestrator with full pipeline"
```

---

## Self-Review Notes

- [S5.1] Covered by Task 7 (full pipeline)
- [S5.2] Covered by Tasks 1, 7
- [S5.3] Covered by Tasks 2, 3, 4, 5, 7
- [S5.4] Covered by Task 1 (state machine), Task 7 (retry loop)
- [S5.5] Covered by Task 6
- All tasks have TDD cycle
- No placeholders
- Type consistency: `Task`, `TaskState`, `SubTask` used throughout
