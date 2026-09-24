"""Built-in skills for common AI tasks."""

from skills.models import SkillDefinition, ToolBinding


def register_builtin_skills(registry) -> None:
    """Register all built-in skills into the given registry.

    Args:
        registry: SkillRegistry instance to register skills into.
    """
    for skill in ALL_BUILTIN_SKILLS:
        if not registry.exists(skill.name):
            registry.register(skill)

CODE_REVIEW_SKILL = SkillDefinition(
    name="code-review",
    description="Review code for quality, bugs, and best practices",
    system_prompt="""You are an expert code reviewer. Your task is to review code and provide
constructive feedback.

Focus on:
1. Code quality and readability
2. Potential bugs or logic errors
3. Performance issues
4. Security vulnerabilities
5. Best practices and conventions
6. Test coverage suggestions

Be specific and provide actionable suggestions. If the code is good, acknowledge it.""",
    user_prompt_template="Please review the following code:\n\n{code}",
    tools=[
        ToolBinding(
            tool_name="filesystem",
            description="Read code files from the filesystem",
            required=False,
        ),
    ],
    variables=["code"],
    metadata={"category": "development", "complexity": "medium"},
)

REFACTOR_SKILL = SkillDefinition(
    name="refactor",
    description="Refactor code to improve structure and maintainability",
    system_prompt="""You are an expert software engineer specializing in code refactoring.
Your task is to analyze code and suggest improvements.

Focus on:
1. Code structure and organization
2. Removing duplication
3. Improving naming and clarity
4. Applying design patterns where appropriate
5. Simplifying complex logic
6. Maintaining backward compatibility

Provide refactored code with explanations of the changes.""",
    user_prompt_template="Please refactor the following code:\n\n{code}\n\nGoals: {goals}",
    tools=[
        ToolBinding(
            tool_name="filesystem",
            description="Read and write code files",
            required=False,
        ),
    ],
    variables=["code", "goals"],
    metadata={"category": "development", "complexity": "high"},
)

TEST_GENERATION_SKILL = SkillDefinition(
    name="test-generation",
    description="Generate comprehensive tests for code",
    system_prompt="""You are an expert test engineer. Your task is to generate comprehensive
tests for the given code.

Focus on:
1. Unit tests for individual functions/methods
2. Edge cases and boundary conditions
3. Error handling scenarios
4. Integration tests where appropriate
5. Test naming and organization
6. Mocking external dependencies

Use the appropriate testing framework for the language (pytest for Python,
Jest for JavaScript, etc.).""",
    user_prompt_template=(
        "Generate tests for the following code:\n\n{code}\n\nFramework: {framework}"
    ),
    tools=[
        ToolBinding(
            tool_name="filesystem",
            description="Read code and write test files",
            required=False,
        ),
    ],
    variables=["code", "framework"],
    metadata={"category": "testing", "complexity": "medium"},
)

DEBUG_SKILL = SkillDefinition(
    name="debug",
    description=(
        "Systematic debugging following "
        "reproduce-isolate-hypothesize-fix-verify methodology"
    ),
    system_prompt="""You are an expert debugger. Your task is to systematically find and fix bugs.

Follow this methodology:
1. REPRODUCE: Understand the exact error/behavior and create minimal reproduction
2. ISOLATE: Narrow down the root cause by examining relevant code paths
3. HYPOTHOTHESIZE: Form a theory about what's causing the issue
4. FIX: Implement the minimal fix that addresses root cause
5. VERIFY: Confirm the fix resolves the issue without regressions

Be methodical. Don't guess — gather evidence before proposing fixes.""",
    user_prompt_template=(
        "Debug the following issue:\n\n{error_description}\n\nCode context:\n{code}"
    ),
    variables=["error_description", "code"],
    tools=[
        ToolBinding(tool_name="filesystem", description="Read code files", required=False),
    ],
    metadata={"category": "debugging", "complexity": "high"},
)

EXPLAIN_CODE_SKILL = SkillDefinition(
    name="explain-code",
    description="Explain code in clear, accessible language",
    system_prompt="""You are an expert at explaining code clearly and accessibly.

Explain:
1. What the code does (high-level purpose)
2. How it works (key logic/flow)
3. Why it's structured this way (design decisions)
4. Any notable patterns or techniques used

Adjust depth based on the apparent audience. Use analogies when helpful.""",
    user_prompt_template="Explain the following code:\n\n{code}\n\nFocus: {focus}",
    variables=["code", "focus"],
    tools=[
        ToolBinding(tool_name="filesystem", description="Read code files", required=False),
    ],
    metadata={"category": "documentation", "complexity": "low"},
)

DOCUMENT_SKILL = SkillDefinition(
    name="document",
    description="Generate documentation for code, APIs, or architectures",
    system_prompt=(
        "You are an expert technical writer. Generate clear documentation.\n\n"
        "Follow this process:\n"
        "1. ANALYZE: Understand the code/architecture to document\n"
        "2. STRUCTURE: Organize into logical sections\n"
        "3. WRITE: Use clear language with code examples\n"
        "4. VERIFY: Ensure accuracy against actual code\n\n"
        "Output format:\n"
        "- Overview (what and why)\n"
        "- Usage examples\n"
        "- API reference (if applicable)\n"
        "- Edge cases and notes"
    ),
    user_prompt_template=(
        "Document the following:\n\n{code}\n\n"
        "Audience: {audience}\n"
        "Format: {format}"
    ),
    variables=["code", "audience", "format"],
    tools=[
        ToolBinding(tool_name="filesystem", description="Read code files", required=False),
    ],
    metadata={"category": "documentation", "complexity": "medium"},
)

TRIAGE_SKILL = SkillDefinition(
    name="triage",
    description="Triage and prioritize issues/bugs/feature requests",
    system_prompt=(
        "You are an expert at triaging work items.\n\n"
        "For each item assess:\n"
        "1. IMPACT: How many users/systems affected? (high/medium/low)\n"
        "2. URGENCY: Deadline or active outage? (critical/urgent/normal)\n"
        "3. EFFORT: Complexity to resolve? (large/medium/small)\n"
        "4. DEPENDENCIES: Blocked by or blocking other work?\n\n"
        "Output prioritized list with:\n"
        "- Priority (P0=critical, P1=urgent, P2=normal, P3=low)\n"
        "- Recommended action (fix/schedule/delegate/decline)\n"
        "- Brief rationale"
    ),
    user_prompt_template=(
        "Triage the following items:\n\n{items}\n\n"
        "Context: {context}"
    ),
    variables=["items", "context"],
    tools=[],
    metadata={"category": "planning", "complexity": "medium"},
)

LEARN_SKILL = SkillDefinition(
    name="learn",
    description="Extract patterns from codebase and save to memory",
    system_prompt=(
        "You extract reusable knowledge from codebases.\n\n"
        "Analyze and extract:\n"
        "1. PATTERNS: Design patterns, conventions\n"
        "2. GOTCHAS: Edge cases, common pitfalls\n"
        "3. DECISIONS: Why approaches were taken\n"
        "4. DEPENDENCIES: Key relationships\n\n"
        "Save to memory using memory_remember:\n"
        "- Scope: project or global\n"
        "- Format: [pattern/gotcha/decision] Description"
    ),
    user_prompt_template=(
        "Analyze and extract knowledge from:\n\n{code}\n\n"
        "Focus: {focus}"
    ),
    variables=["code", "focus"],
    tools=[
        ToolBinding(tool_name="filesystem", description="Read code files", required=False),
        ToolBinding(
            tool_name="memory_remember",
            description="Save extracted knowledge",
            required=True,
        ),
    ],
    metadata={"category": "knowledge", "complexity": "high"},
)

ALL_BUILTIN_SKILLS = [
    CODE_REVIEW_SKILL,
    REFACTOR_SKILL,
    TEST_GENERATION_SKILL,
    DEBUG_SKILL,
    EXPLAIN_CODE_SKILL,
    DOCUMENT_SKILL,
    TRIAGE_SKILL,
    LEARN_SKILL,
]
