"""Built-in skills for common AI tasks."""

from skills.models import SkillDefinition, ToolBinding

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

ALL_BUILTIN_SKILLS = [
    CODE_REVIEW_SKILL,
    REFACTOR_SKILL,
    TEST_GENERATION_SKILL,
]
