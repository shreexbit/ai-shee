import json
import re

from context import Context


def parse_json_response(response):
    """
    Parse JSON returned by an LLM.

    Accepts:
    1. Plain JSON
    2. JSON wrapped in ```json ... ```
    3. JSON surrounded by small amounts of explanatory text

    Returns:
        Parsed JSON object or None if parsing fails.
    """

    if not response:
        return None

    response = response.strip()

    # First try strict JSON.
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Remove markdown code fences.
    fenced = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        response,
        re.DOTALL | re.IGNORECASE
    )

    if fenced:
        candidate = fenced.group(1).strip()

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Try to locate a JSON object inside surrounding text.
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end > start:
        candidate = response[start:end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


class ToolLoop:

    def __init__(
        self,
        llm,
        tool_executor,
        max_steps=10
    ):

        self.llm = llm
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.context = Context()

    def run(self, task):

        self.context.set_task(task)

        messages = [

            {
                "role": "system",

                "content": """
You are a tool-using coding agent.

You investigate software-engineering tasks
by using the available tools.

Available tools:

1. search_code
   Search the repository for a piece of code.

2. read_file
   Read a repository file.

3. run_command
   Execute an approved terminal command.

Return ONLY valid JSON.

To use a tool:

{
    "action": "tool",
    "tool": "tool_name",
    "arguments": {}
}

When investigation is complete:

{
    "action": "finish"
}

Do not write code changes.

Your job is investigation only.

Use previous tool results as evidence.

Avoid repeating the same tool call unless
there is a clear reason to do so.
"""
            },

            {
                "role": "user",

                "content":
                    "Investigate this task:\n\n"
                    + json.dumps(
                        task,
                        indent=2
                    )
            }
        ]

        for step in range(
            1,
            self.max_steps + 1
        ):

            print(
                f"\n--- TOOL LOOP STEP "
                f"{step} ---"
            )

            response = self.llm.generate(
                messages
            )

            print(
                "\nLLM DECISION:"
            )

            print(
                response
            )

            decision = parse_json_response(
                response
            )

            if decision is None:

                print(
                    "\nInvalid tool decision."
                )

                return {
                    "success": False,
                    "steps": step,
                    "results":
                        self.context.tool_history,
                    "context":
                        self.context.snapshot()
                }

            if not isinstance(
                decision,
                dict
            ):

                print(
                    "\nInvalid decision format."
                )

                return {
                    "success": False,
                    "steps": step,
                    "results":
                        self.context.tool_history,
                    "context":
                        self.context.snapshot()
                }

            action = decision.get(
                "action"
            )

            if action == "finish":

                print(
                    "\nTOOL LOOP FINISHED"
                )

                return {
                    "success": True,
                    "steps": step,
                    "results":
                        self.context.tool_history,
                    "context":
                        self.context.snapshot()
                }

            if action != "tool":

                print(
                    "\nUnknown agent action:"
                )

                print(
                    action
                )

                return {
                    "success": False,
                    "steps": step,
                    "results":
                        self.context.tool_history,
                    "context":
                        self.context.snapshot()
                }

            tool_name = decision.get(
                "tool"
            )

            arguments = decision.get(
                "arguments",
                {}
            )

            if not isinstance(
                arguments,
                dict
            ):

                print(
                    "\nInvalid tool arguments."
                )

                return {
                    "success": False,
                    "steps": step,
                    "results":
                        self.context.tool_history,
                    "context":
                        self.context.snapshot()
                }

            print(
                f"\nEXECUTING TOOL: "
                f"{tool_name}"
            )

            print(
                f"ARGUMENTS: "
                f"{arguments}"
            )

            if self.context.has_used_tool(
                tool_name,
                arguments
            ):

                print(
                    "\nMEMORY: This exact "
                    "tool call was already made."
                )

            result = (
                self.tool_executor.execute(
                    decision
                )
            )

            print(
                "\nTOOL RESULT:"
            )

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            self.context.add_tool_result(
                tool_name,
                arguments,
                result
            )

            messages.append(
                {
                    "role": "assistant",
                    "content": response
                }
            )

            recent_history = (
                self.context.get_recent_tool_history(
                    limit=3
                )
            )

            memory = {
                "task": self.context.task,
                "hypothesis": self.context.hypothesis,
                "relevant_files": self.context.relevant_files,
                "failed_approaches": self.context.failed_approaches[-3:],
                "observations": self.context.observations[-5:],
                "recent_tool_history": recent_history
            }

            messages.append(
                {
                    "role": "user",
                    "content": (
                        "CURRENT TOOL RESULT:\n\n"
                        + json.dumps(
                            result,
                            indent=2
                        )
                        + "\n\n"
                        "RELEVANT MEMORY:\n\n"
                        + json.dumps(
                            memory,
                            indent=2
                        )
                        + "\n\n"
                        "Use the evidence above to decide "
                        "your next action. Avoid repeating "
                        "previous tool calls unless necessary."
                    )
                }
            )

        return {
            "success": False,
            "steps": self.max_steps,
            "results":
                self.context.tool_history,
            "context":
                self.context.snapshot()
        }


if __name__ == "__main__":

    from llm import LLM
    from agent import ToolExecutor

    llm = LLM()

    tool_executor = ToolExecutor(
        "test_repo"
    )

    loop = ToolLoop(
        llm,
        tool_executor
    )

    result = loop.run(
        {
            "goal":
                "Investigate division by zero"
        }
    )

    print(
        "\n=== FINAL TOOL LOOP RESULT ==="
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )