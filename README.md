AI-SHEE
Autonomous Coding Harness

AI-SHEE is an autonomous coding-agent harness focused on one goal:

Don't stop when code is generated. Stop when there is evidence that it works.

It combines repository intelligence, tool use, context management, verification, and failure recovery.

Architecture
Issue
  ↓
Task Analysis
  ↓
Repository Map + Search
  ↓
Tool Loop
  ↓
Code Plan
  ↓
Apply Changes
  ↓
Verification
  ↓
 ┌───────────────┐
 │               │
PASS            FAIL
 │               │
 ↓               ↓
DONE       Recovery Analysis
                 ↓
           Fresh Context
                 ↓
           Recovery Plan
                 ↓
              Verify
Core Components
Task Analyzer

Converts the issue into a structured goal, requirements, verification
criteria, and search terms.

Repository Intelligence

Builds a lightweight repository map and ranks relevant code-search
results so the model receives focused context.

Tool Loop

The model can autonomously use:

search_code
read_file
run_command

Tool history is bounded to keep context focused.

Context Management

Tracks relevant files, tool history, observations, changes, test results,
and failed approaches.

During recovery, AI-SHEE re-reads the current repository state instead of
reusing stale information from a failed attempt.

Code Planner

Produces structured changes containing the target file, operation, reason,
and replacement or rewritten content.

For replacements, old_text must come from the current repository state.

Verification & Recovery

AI-SHEE verifies changes after implementation.

If verification fails, the failure output is analyzed and used to generate a
new recovery plan. The repository is then verified again.

Demonstrated Recovery

The included calculator example demonstrates:

Initial implementation
        ↓
Local tests PASS
        ↓
Independent evaluator FAILS
        ↓
Failure analysis
        ↓
Fresh repository context
        ↓
Recovery
        ↓
Independent tests PASS

The demonstrated failure is division by zero: the initial implementation
returns 0, while the independent evaluator requires ValueError.

Safety
Controlled command execution
Dangerous command/operator rejection
Repository path validation
Protected evaluator directories
Exact text replacement
Backups before modifications
Configuration
export REPOSITORY_PATH=/path/to/repository
export ISSUE="Fix the authentication bug"
export AI_MODE=real
export AI_API_KEY="your-api-key"
export AI_BASE_URL="your-api-base-url"
export AI_MODEL="your-model"

No secrets are stored in the repository.

Running
make setup
make run
make test
make clean
Local Independent-Evaluator Demo
export AI_MODE=mock
export REPOSITORY_PATH=test_repo
export INDEPENDENT_TEST_PATH=eval_tests
make run

INDEPENDENT_TEST_PATH enables independent verification. Without it,
independent verification is skipped.

A successful run ends with:

=== AI-SHEE SUCCESS ===
Evaluation Interface

The repository provides:

make setup
make run
make test
make clean

The model configuration, repository, and issue can be supplied externally
through environment variables.

Project Structure
ai-shee/
├── Makefile
├── README.md
├── requirements.txt
├── src/
│   ├── main.py
│   ├── llm.py
│   ├── agent.py
│   ├── tools.py
│   ├── context.py
│   ├── verifier.py
│   ├── recovery.py
│   └── tool_loop.py
├── eval_tests/
│   └── test_calculator.py
└── test_repo/
    ├── calculator.py
    └── test_calculator.py
Design Principles

Correctness First — verification is evidence of success.

Evidence Over Claims — tool and test results drive subsequent
decisions.

Recovery Over Repetition — failures trigger analysis before retrying.

Focused Context — relevant repository information is prioritized.

Safe Tool Execution — model actions pass through controlled tools.
