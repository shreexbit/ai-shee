import json
import os

from llm import LLM
from tools import (
    build_repository_map,
    search_code,
    read_file,
    edit_file,
    replace_text,
    run_command,
)
from context import Context
from recovery import Recovery


class ToolExecutor:

    def __init__(self, repository_path):

        self.repository_path = repository_path

    def _normalize_path(self, path):

        if not path:
            return path

        prefix = (
            self.repository_path.rstrip("/")
            + "/"
        )

        if path.startswith(prefix):

            return path[
                len(prefix):
            ]

        return path

    def execute(self, decision):

        tool = decision.get("tool")

        arguments = decision.get(
            "arguments",
            {}
        )

        if tool == "search_code":

            query = arguments.get(
                "query",
                ""
            )

            results = search_code(
                query,
                self.repository_path
            )

            normalized_results = []

            for item in results:

                item = dict(item)

                item["file"] = (
                    self._normalize_path(
                        item["file"]
                    )
                )

                normalized_results.append(
                    item
                )

            return {
                "success": True,
                "tool": "search_code",
                "result":
                    normalized_results
            }

        if tool == "read_file":

            path = arguments.get(
                "path"
            )

            path = self._normalize_path(
                path
            )

            if not path:

                return {
                    "success": False,
                    "error":
                        "Missing file path"
                }

            full_path = os.path.join(
                self.repository_path,
                path
            )

            return {
                "success": True,
                "tool": "read_file",
                "result": read_file(
                    full_path
                )
            }

        if tool == "run_command":

            command = arguments.get(
                "command",
                ""
            )

            return {
                "success": True,
                "tool": "run_command",
                "result": run_command(
                    command,
                    self.repository_path
                )
            }

        if tool == "edit_file":

            path = arguments.get(
                "path"
            )

            new_content = arguments.get(
                "new_content"
            )

            path = self._normalize_path(
                path
            )

            if not path:

                return {
                    "success": False,
                    "error":
                        "Missing file path"
                }

            if new_content is None:

                return {
                    "success": False,
                    "error":
                        "Missing new_content"
                }

            full_path = os.path.join(
                self.repository_path,
                path
            )

            return edit_file(
                full_path,
                new_content,
                self.repository_path
            )

        if tool == "replace_text":

            path = arguments.get(
                "path"
            )

            old_text = arguments.get(
                "old_text"
            )

            new_text = arguments.get(
                "new_text"
            )

            path = self._normalize_path(
                path
            )

            if not path:

                return {
                    "success": False,
                    "error":
                        "Missing file path"
                }

            if old_text is None:

                return {
                    "success": False,
                    "error":
                        "Missing old_text"
                }

            if new_text is None:

                return {
                    "success": False,
                    "error":
                        "Missing new_text"
                }

            full_path = os.path.join(
                self.repository_path,
                path
            )

            return replace_text(
                full_path,
                old_text,
                new_text,
                self.repository_path
            )

        return {
            "success": False,
            "error":
                f"Unknown tool: {tool}"
        }




class TaskAnalyzer:

    def __init__(self, llm):

        self.llm = llm

    def analyze(self, task):

        prompt = f"""
Analyze this software engineering task.

TASK:
{task}

Return ONLY valid JSON:

{{
    "goal": "...",
    "requirements": [],
    "verification": [],
    "search_terms": [],
    "status": "NEEDS_INVESTIGATION"
}}
"""

        response = self.llm.generate(
            [
                {
                    "role": "system",
                    "content":
                        "You are a task analyzer."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {
                "goal": task,
                "requirements": [],
                "verification": [],
                "search_terms": [],
                "status":
                    "NEEDS_INVESTIGATION"
            }


class CodePlanner:

    def __init__(self, llm):

        self.llm = llm

    def plan(
        self,
        task,
        files,
        terminal_context=None,
        recovery_context=None
    ):

        prompt = f"""
You are planning code changes for a software
engineering task.

TASK:
{json.dumps(task, indent=2)}

RELEVANT FILES:
{json.dumps(files, indent=2)}

TERMINAL CONTEXT:
{json.dumps(
    terminal_context or {},
    indent=2
)}

PREVIOUS RECOVERY INFORMATION:
{json.dumps(
    recovery_context or {},
    indent=2
)}

Return ONLY valid JSON:

{{
    "changes": [
        {{
            "file": "...",
            "operation": "replace",
            "reason": "...",
            "old_text": "...",
            "new_text": "..."
        }}
    ]
}}

Rules:

1. Only modify files relevant to the task.
2. Preserve unrelated functionality.
3. Prefer "replace" when a precise existing
   code fragment can be safely changed.
4. For "replace", old_text MUST match exactly
   one existing fragment in the file.
5. Use "rewrite" only when a precise replacement
   is not appropriate.
6. For "rewrite", provide "new_content".
7. Use test evidence when available.
8. If recovery information exists, fix
   the previously identified failure.
9. Include tests when appropriate.
10. Never modify evaluator-owned files.
"""

        response = self.llm.generate(
            [
                {
                    "role": "system",
                    "content":
                        "You are a code-change planner."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        try:

            return json.loads(response)

        except json.JSONDecodeError:

            return {
                "changes": []
            }




class Evaluator:
    def __init__(self, repository_path):
        self.repository_path = repository_path

    def run(self):
        return run_command("pytest", self.repository_path)

    def run_independent(self):
        import os

        evaluation_path = os.getenv("INDEPENDENT_TEST_PATH")

        if not evaluation_path:
            return {
                "success": True,
                "skipped": True,
                "reason": "No independent evaluator configured"
            }

        if not os.path.exists(evaluation_path):
            return {
                "success": True,
                "skipped": True,
                "reason": f"Independent evaluator not found: {evaluation_path}"
            }

        return run_command("pytest", evaluation_path)


class Agent:

    def __init__(
        self,
        llm,
        repository_path
    ):

        self.llm = llm

        self.repository_path = (
            repository_path
        )

        self.context = Context()

        self.analyzer = TaskAnalyzer(
            llm
        )

        self.planner = CodePlanner(
            llm
        )

        self.evaluator = Evaluator(
            repository_path
        )

        self.recovery = Recovery(
            llm
        )

        self.tool_executor = ToolExecutor(
            repository_path
        )

    def apply_change(self, change):

        path = change.get(
            "file"
        )

        if not path:
            return {
                "success": False,
                "error": "Missing file"
            }

        repo_path = os.path.abspath(
            self.repository_path
        )

        repo_name = os.path.basename(
            repo_path
        )

        normalized_path = path.replace(
            "\\",
            "/"
        )

        repo_prefix = (
            repo_name.rstrip("/")
            + "/"
        )

        if normalized_path.startswith(
            repo_prefix
        ):
            normalized_path = normalized_path[
                len(repo_prefix):
            ]

        path = normalized_path

        operation = change.get(
            "operation",
            "rewrite"
        )

        if operation == "replace":

            old_text = change.get(
                "old_text"
            )

            new_text = change.get(
                "new_text"
            )

            if old_text is None or new_text is None:
                return {
                    "success": False,
                    "file": path,
                    "error":
                        "Missing old_text or new_text"
                }

            full_path = os.path.join(
                self.repository_path,
                path
            )

            return replace_text(
                full_path,
                old_text,
                new_text,
                self.repository_path
            )

        if operation == "rewrite":

            new_content = change.get(
                "new_content"
            )

            if new_content is None:
                return {
                    "success": False,
                    "file": path,
                    "error": "Missing new_content"
                }

            full_path = os.path.join(
                self.repository_path,
                path
            )

            return edit_file(
                full_path,
                new_content,
                self.repository_path
            )

        return {
            "success": False,
            "file": path,
            "error":
                f"Unknown change operation: {operation}"
        }

    def investigate(self, issue):

        print(
            "\n=== AI-SHEE START ==="
        )

        analysis = self.analyzer.analyze(
            issue
        )

        print(
            "\n--- TASK ANALYSIS ---"
        )

        print(
            json.dumps(
                analysis,
                indent=2
            )
        )

        self.context.set_task(
            analysis
        )

        print(
            "\n--- REPOSITORY MAP ---"
        )

        repo_map = build_repository_map(
            self.repository_path
        )

        print(
            json.dumps(
                repo_map,
                indent=2
            )
        )

        search_terms = analysis.get(
            "search_terms",
            []
        )

        ranked = []

        for term in search_terms:

            results = search_code(
                term,
                self.repository_path
            )

            ranked.extend(
                results
            )

        ranked.sort(
            key=lambda x:
                x.get("score", 0),
            reverse=True
        )

        selected = []

        for item in ranked:

            path = item["file"]

            if path not in selected:

                selected.append(path)

            if len(selected) >= 5:

                break

        print(
            "\n--- SELECTED CONTEXT ---"
        )

        files = {}

        for path in selected:

            self.context.add_relevant_file(
                path
            )

            content = read_file(
                path
            )

            files[path] = content

        print(
            json.dumps(
                files,
                indent=2
            )
        )

        print(
            "\n--- TOOL LOOP ---"
        )

        from tool_loop import ToolLoop

        tool_loop = ToolLoop(
            self.llm,
            self.tool_executor
        )

        investigation = tool_loop.run(
            analysis
        )

        print(
            "\n--- INVESTIGATION RESULT ---"
        )

        print(
            json.dumps(
                investigation,
                indent=2
            )
        )

        investigation_results = investigation.get(
            "results",
            []
        )

        terminal_context = {
            "tool_history": investigation_results[-6:]
        }

        print(
            "\n--- CODE CHANGE PLAN ---"
        )

        plan = self.planner.plan(
            analysis,
            files,
            terminal_context
        )

        print(
            json.dumps(
                plan,
                indent=2
            )
        )

        application_results = []
        application_failed = False

        for change in plan.get(
            "changes",
            []
        ):

            path = change.get(
                "file",
                "<unknown>"
            )

            print(
                f"\nApplying change: {path}"
            )

            result = self.apply_change(
                change
            )

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            application_results.append(
                result
            )

            self.context.add_change(
                change
            )

            if not result.get(
                "success",
                False
            ):
                application_failed = True

                self.context.add_failed_approach(
                    f"Change application failed for {path}: "
                    f"{result.get('message') or result.get('error')}"
                )

        print(
            "\n--- VERIFICATION ---"
        )

        test_result = (
            self.evaluator.run()
        )

        print(
            json.dumps(
                test_result,
                indent=2
            )
        )

        if application_failed:
            test_result = {
                **test_result,
                "success": False,
                "change_application_failed": True,
                "application_results": application_results
            }

            print(
                "\n--- CHANGE APPLICATION FAILED ---"
            )

            print(
                "At least one planned change was not applied successfully."
            )

        self.context.add_test_result(
            test_result
        )

        print(
            "\n--- INDEPENDENT VERIFICATION ---"
        )

        independent_result = (
            self.evaluator.run_independent()
        )

        print(
            json.dumps(
                independent_result,
                indent=2
            )
        )

        test_result["independent"] = (
            independent_result
        )

        if (not independent_result.get("skipped", False)
        and not independent_result.get("success", False)):
            test_result["success"] = False

        self.context.add_test_result(
            test_result
        )

        if test_result.get(
            "success"
        ):

            print(
                "\n=== AI-SHEE SUCCESS ==="
            )

            return True

        print(
            "\n=== VERIFICATION FAILED ==="
        )

        recovery_info = (
            self.recovery.analyze_failure(
                analysis,
                test_result,
                files
            )
        )

        print(
            "\n--- RECOVERY ANALYSIS ---"
        )

        print(
            json.dumps(
                recovery_info,
                indent=2
            )
        )

        if not recovery_info.get(
            "should_retry",
            False
        ):

            print(
                "\nRecovery decided not to retry."
            )

            return False

        for change in reversed(
            plan.get("changes", [])
        ):

            path = change["file"]

            from tools import restore_file

            restore_file(
                path
            )

        self.context.add_failed_approach(
            recovery_info
        )

        print(
            "\n--- RECOVERY PLAN ---"
        )

        recovery_plan = self.planner.plan(
            analysis,
            files,
            terminal_context,
            recovery_info
        )

        print(
            json.dumps(
                recovery_plan,
                indent=2
            )
        )

        recovery_application_failed = False

        for change in recovery_plan.get(
            "changes",
            []
        ):

            path = change.get(
                "file",
                "<unknown>"
            )

            print(
                f"\\nApplying recovery change: {path}"
            )

            result = self.apply_change(
                change
            )

            print(
                json.dumps(
                    result,
                    indent=2
                )
            )

            if not result.get(
                "success",
                False
            ):
                recovery_application_failed = True

                self.context.add_failed_approach(
                    f"Recovery change failed for {path}: "
                    f"{result.get('message') or result.get('error')}"
                )

        print(
            "\n--- FINAL VERIFICATION ---"
        )

        final_result = (
            self.evaluator.run()
        )

        print(
            json.dumps(
                final_result,
                indent=2
            )
        )

        print(
            "\n--- FINAL INDEPENDENT VERIFICATION ---"
        )

        final_independent_result = (
            self.evaluator.run_independent()
        )

        print(
            json.dumps(
                final_independent_result,
                indent=2
            )
        )

        final_result["independent"] = (
            final_independent_result
        )

        if recovery_application_failed:
            final_result["success"] = False

        if (not final_independent_result.get("skipped", False)
            and not final_independent_result.get("success", False)):
            final_result["success"] = False

        if final_result.get(
            "success"
        ):

            print(
                "\n=== AI-SHEE SUCCESS ==="
            )

            return True

        print(
            "\n=== AI-SHEE FAILED ==="
        )

        return False


if __name__ == "__main__":

    main_llm = LLM()

    agent = Agent(
        main_llm,
        "test_repo"
    )

    agent.investigate(
        """
Fix the divide function so it handles
division by zero.

Add an appropriate test.
"""
    )
