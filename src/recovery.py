import json


class Recovery:
    def __init__(self, llm):
        self.llm = llm

    def analyze_failure(self, task, test_result, files):
        """
        Analyze a failed test and suggest the next action.
        Does not modify any files.
        """

        prompt = f"""
An autonomous coding agent attempted to solve a task,
but verification failed.

ORIGINAL TASK:
{json.dumps(task, indent=2)}

TEST RESULTS:
{json.dumps(test_result, indent=2)}

FILES PREVIOUSLY INVESTIGATED:
{json.dumps(files, indent=2)}

Analyze the failure.

Return ONLY valid JSON:

{{
    "failure_reason": "...",
    "next_action": "...",
    "search_terms": ["..."],
    "should_retry": true
}}

Rules:
1. Use the actual test output as evidence.
2. Do not assume the previous fix was correct.
3. Identify the most likely cause of failure.
4. Suggest a concrete next action.
5. Do not write replacement code yet.
"""

        response = self.llm.generate([
            {
                "role": "system",
                "content": (
                    "You are the failure-recovery analyst "
                    "for an autonomous coding agent."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ])

        try:
            result = json.loads(response)

            required = {
                "failure_reason",
                "next_action",
                "search_terms",
                "should_retry"
            }

            if not required.issubset(result):
                raise ValueError("Incomplete recovery response")

            return result

        except (json.JSONDecodeError, ValueError):
            return {
                "failure_reason": "Unable to analyze failure",
                "next_action": "Request further investigation",
                "search_terms": [],
                "should_retry": False
            }