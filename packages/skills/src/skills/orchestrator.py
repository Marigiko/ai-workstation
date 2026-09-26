"""Multi-step task orchestrator.

Decomposes complex tasks into sub-tasks and executes them sequentially,
routing each sub-task to the appropriate specialized agent.
"""

import logging
from typing import Any

from providers import BaseProvider
from routing import AgentRouter

from contracts import CompletionRequest, Message, Role

logger = logging.getLogger(__name__)


class TaskStep:
    """A single step in a multi-step task."""

    def __init__(self, description: str, depends_on: list[int] | None = None):
        self.description = description
        self.depends_on = depends_on or []
        self.result: str | None = None
        self.status: str = "pending"


class TaskOrchestrator:
    """Orchestrates multi-step task execution.

    Decomposes complex tasks into sub-tasks using an LLM,
    then executes each sub-task with the appropriate agent.
    """

    def __init__(
        self,
        provider: BaseProvider,
        agent_router: AgentRouter,
        max_steps: int = 10,
    ):
        self.provider = provider
        self.agent_router = agent_router
        self.max_steps = max_steps

    async def decompose_task(self, task_description: str) -> list[TaskStep]:
        """Decompose a complex task into sub-tasks using an LLM."""
        prompt = f"""Decompose the following task into sequential sub-tasks.
Each sub-task should be a clear, actionable step.
Return a JSON array of objects with "description" and optional "depends_on" (array of step indices).

Task: {task_description}

Return ONLY the JSON array, no other text."""

        request = CompletionRequest(
            messages=[Message(role=Role.USER, content=prompt)],
            temperature=0.3,
        )

        response = await self.provider.complete(request)

        import json
        try:
            steps_data = json.loads(response.content)
            steps = []
            for step_data in steps_data:
                step = TaskStep(
                    description=step_data.get("description", ""),
                    depends_on=step_data.get("depends_on", []),
                )
                steps.append(step)
            return steps[:self.max_steps]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to parse task decomposition: %s", e)
            return [TaskStep(description=task_description)]

    async def execute_step(self, step: TaskStep, previous_results: list[str]) -> str:
        """Execute a single task step."""
        context = ""
        if previous_results:
            context = "\n\nPrevious results:\n" + "\n".join(
                f"Step {i+1}: {result}" for i, result in enumerate(previous_results)
            )

        request = CompletionRequest(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content=(
                        "You are executing a step of a multi-step task. "
                        "Complete the step using the context provided."
                    ),
                ),
                Message(
                    role=Role.USER,
                    content=f"Step: {step.description}{context}",
                ),
            ],
        )

        decision = await self.agent_router.resolve(request)
        provider = self.agent_router.registry.get(decision.provider)
        if not provider:
            raise RuntimeError(f"Provider {decision.provider} not found")

        response = await provider.complete(request)
        return response.content

    async def execute(self, task_description: str) -> dict[str, Any]:
        """Execute a multi-step task.

        Returns:
            Dict with 'steps' (list of step descriptions and results),
            'final_result' (concatenation of all results), and 'metadata'.
        """
        logger.info("Decomposing task: %s", task_description[:100])
        steps = await self.decompose_task(task_description)
        logger.info("Task decomposed into %d steps", len(steps))

        results: list[str] = []
        step_outputs: list[dict[str, Any]] = []

        for i, step in enumerate(steps):
            logger.info("Executing step %d/%d: %s", i + 1, len(steps), step.description[:50])

            try:
                step.status = "running"
                result = await self.execute_step(step, results)
                step.result = result
                step.status = "completed"
                results.append(result)

                step_outputs.append({
                    "step": i + 1,
                    "description": step.description,
                    "result": result,
                    "status": "completed",
                })

            except Exception as e:
                logger.error("Step %d failed: %s", i + 1, e, exc_info=True)
                step.status = "failed"
                step_outputs.append({
                    "step": i + 1,
                    "description": step.description,
                    "error": str(e),
                    "status": "failed",
                })
                results.append(f"[FAILED: {e}]")

        final_result = "\n\n".join(results)

        return {
            "steps": step_outputs,
            "final_result": final_result,
            "metadata": {
                "total_steps": len(steps),
                "completed_steps": sum(1 for s in step_outputs if s["status"] == "completed"),
                "failed_steps": sum(1 for s in step_outputs if s["status"] == "failed"),
            },
        }
