import os

from llm import LLM
from agent import Agent


def main():
    repository_path = os.getenv("REPOSITORY_PATH", "test_repo")

    issue = os.getenv("ISSUE")

    if not issue:
        issue = """
Fix the bug described by the evaluator.
Investigate the repository, identify the root cause,
implement the smallest correct change, and verify it with tests.
"""

    print("=== AI-SHEE START ===")
    print(f"Repository: {repository_path}")
    print(f"Issue: {issue.strip()}")

    llm = LLM()
    agent = Agent(llm, repository_path)

    result = agent.investigate(issue)

    if result:
        print("\n=== AI-SHEE SUCCESS ===")
    else:
        print("\n=== AI-SHEE FAILED ===")


if __name__ == "__main__":
    main()