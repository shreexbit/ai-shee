class Context:

    def __init__(self):

        self.task = None

        self.relevant_files = []

        self.hypothesis = None

        self.changes = []

        self.test_results = []

        self.failed_approaches = []

        self.tool_history = []

        self.observations = []

    def set_task(self, task):

        self.task = task

    def add_relevant_file(self, file_path):

        if file_path not in self.relevant_files:

            self.relevant_files.append(
                file_path
            )

    def add_change(self, change):

        self.changes.append(
            change
        )

    def add_test_result(self, result):

        self.test_results.append(
            result
        )

    def add_failed_approach(self, approach):

        self.failed_approaches.append(
            approach
        )

    def add_tool_result(
        self,
        tool,
        arguments,
        result
    ):

        self.tool_history.append(
            {
                "tool": tool,
                "arguments": arguments,
                "result": result
            }
        )

    def add_observation(self, observation):

        self.observations.append(
            observation
        )

    def has_used_tool(
        self,
        tool,
        arguments
    ):

        for item in self.tool_history:

            if (
                item["tool"] == tool
                and item["arguments"] == arguments
            ):

                return True

        return False

    def get_recent_tool_history(
        self,
        limit=5
    ):

        return self.tool_history[-limit:]

    def snapshot(self):

        return {
            "task": self.task,

            "relevant_files":
                self.relevant_files,

            "hypothesis":
                self.hypothesis,

            "changes":
                self.changes,

            "test_results":
                self.test_results,

            "failed_approaches":
                self.failed_approaches,

            "tool_history":
                self.tool_history,

            "observations":
                self.observations
        }