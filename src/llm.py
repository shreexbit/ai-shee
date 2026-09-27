import json
import os

from openai import OpenAI


class LLM:

    def __init__(self):

        self.mode = os.getenv("AI_MODE",
            "real" if os.getenv("AI_API_KEY") else "mock")

        self.plan_calls = 0
        self.tool_calls = 0

        if self.mode == "real":

            self.api_key = os.getenv(
                "AI_API_KEY"
            )

            self.model = os.getenv(
                "AI_MODEL",
                "deepseek-flash"
            )

            self.base_url = os.getenv(
                "AI_BASE_URL",
                "https://api.deepseek.com"
            )

            if not self.api_key:

                raise RuntimeError(
                    "AI_API_KEY is not set"
                )

            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    def generate(self, messages):

        if self.mode == "mock":

            system_prompt = (
                messages[0]["content"]
                .lower()
            )

            # --------------------------------------------------
            # TASK ANALYZER
            # --------------------------------------------------

            if "task analyzer" in system_prompt:

                return """
{
    "goal": "Fix division by zero in divide()",
    "requirements": [
        "Fix the divide function",
        "Add a regression test"
    ],
    "verification": [
        "Run the relevant tests"
    ],
    "search_terms": [
        "divide",
        "test_divide"
    ],
    "status": "NEEDS_INVESTIGATION"
}
"""

            # --------------------------------------------------
            # TOOL-USE AGENT
            # --------------------------------------------------

            if "tool-using coding agent" in system_prompt:

                self.tool_calls += 1

                # First decision:
                # Search for the relevant code.
                if self.tool_calls == 1:

                    return """
{
    "action": "tool",
    "tool": "search_code",
    "arguments": {
        "query": "divide"
    }
}
"""

                # Second decision:
                # Read the implementation.
                if self.tool_calls == 2:

                    return """
{
    "action": "tool",
    "tool": "read_file",
    "arguments": {
        "path": "test_repo/calculator.py"
    }
}
"""

                # Third decision:
                # Run the existing tests.
                if self.tool_calls == 3:

                    return """
{
    "action": "tool",
    "tool": "run_command",
    "arguments": {
        "command": "pytest"
    }
}
"""

                # Fourth decision:
                # Investigation is complete.
                return """
{
    "action": "finish"
}
"""

            # --------------------------------------------------
            # FAILURE RECOVERY ANALYST
            # --------------------------------------------------

            if "failure-recovery analyst" in system_prompt:

                return """
{
    "failure_reason": "The previous implementation returned 0 for division by zero, but the independent evaluator requires divide() to raise ValueError.",
    "next_action": "Change divide() so that a zero denominator raises ValueError instead of returning 0.",
    "search_terms": [
        "divide",
        "test_divide"
    ],
    "should_retry": true
}
"""

            # --------------------------------------------------
            # CODE CHANGE PLANNER
            # --------------------------------------------------

            if "code-change planner" in system_prompt:

                self.plan_calls += 1

                user_prompt = ""

                if len(messages) > 1:

                    user_prompt = (
                        messages[1]["content"]
                        .lower()
                    )

                has_recovery_context = (
                    "previous recovery information"
                    in user_prompt
                )

                if (
                    self.plan_calls == 1
                    or not has_recovery_context
                ):

                    return """
{
    "changes": [
        {
            "file": "test_repo/calculator.py",
            "operation": "replace",
            "reason": "Attempt to handle division by zero.",
            "old_text": "if b == 0:\\n        return 0",
            "new_text": "if b == 0:\\n        return 0"
        },
        {
            "file": "test_repo/test_calculator.py",
            "operation": "replace",
            "reason": "Add a regression test.",
            "old_text": "def test_divide():\\n    assert divide(10, 2) == 5",
            "new_text": "def test_divide():\\n    assert divide(10, 2) == 5\\n\\n\\ndef test_divide_by_zero():\\n    assert divide(10, 0) == 0"
        }
    ]
}
"""

                return """
{
    "changes": [
        {
            "file": "test_repo/calculator.py",
            "operation": "replace",
            "reason": "Raise ValueError for division by zero.",
            "old_text": "if b == 0:\\n        return 0",
            "new_text": "if b == 0:\\n        raise ValueError(\\\"Cannot divide by zero\\\")"
        },
        {
            "file": "test_repo/test_calculator.py",
            "operation": "replace",
            "reason": "Add a regression test for division by zero.",
            "old_text": "def test_divide():\\n    assert divide(10, 2) == 5\\n\\n\\ndef test_divide_by_zero():\\n    assert divide(10, 0) == 0",
            "new_text": "def test_divide():\\n    assert divide(10, 2) == 5\\n\\n\\n\\ndef test_divide_by_zero():\\n    try:\\n        divide(10, 0)\\n        assert False\\n    except ValueError:\\n        assert True"
        }
    ]
}
"""

        # --------------------------------------------------
        # REAL MODEL
        # --------------------------------------------------

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return (
            response
            .choices[0]
            .message
            .content
        )
