# AI-SHEE

## Autonomous Coding Harness

AI-SHEE is an autonomous coding-agent harness designed to solve software
engineering tasks by combining repository intelligence, tool use,
verification, failure recovery, and context management.

The goal is not simply to generate code.

The goal is to produce a **verified software change**.

---

## Architecture

```text
                    ┌─────────────────┐
                    │      ISSUE      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Task Analyzer  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Repository Map  │
                    │ + Code Search   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Tool Loop     │
                    │ search/read/run │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Code Planner   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Apply Changes │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Verification │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                  PASS              FAIL
                    │                 │
                    ▼                 ▼
                  DONE          ┌─────────────┐
                                │  Recovery   │
                                │   Analysis  │
                                └──────┬──────┘
                                       │
                                       ▼
                                ┌─────────────┐
                                │ Retry Plan  │
                                └──────┬──────┘
                                       │
                                       └──────► Verification

Core Components
1. Task Analyzer

Converts a natural-language software engineering issue into structured
information:

Goal
Requirements
Verification requirements
Search terms
2. Repository Intelligence

AI-SHEE first builds a lightweight repository map and identifies files
that are likely to be relevant to the task.

It then ranks search results so the model receives focused repository
context instead of the entire codebase.

3. Tool Loop

The model can autonomously decide which investigation tool to use.

Available tools include:

search_code
read_file
run_command

Tool results are returned to the model as evidence for the next decision.

The agent also tracks previous tool calls to avoid unnecessary repeated
investigation.

4. Context Memory

AI-SHEE maintains structured context throughout the task.

The context records:

Current task
Relevant files
Tool history
Observations
Changes
Test results
Failed approaches

This allows later decisions to use information discovered earlier in
the task.

5. Code Planner

After investigation, the model creates a structured implementation plan.

Each planned change contains:

Target file
Reason for the change
New file content

Changes are then applied through the controlled file-editing layer.

6. Verification

AI-SHEE does not consider code generation to be success.

After changes are applied, the repository is tested.

The test results become evidence for the next decision.

Code Change
     ↓
Run Tests
     ↓
 ┌───┴───┐
PASS    FAIL
 ↓        ↓
Done   Recovery
Failure Recovery

One of AI-SHEE's main capabilities is recovery from incorrect solutions.

A solution can appear correct to the repository's existing tests while
still violating the actual task requirements.

AI-SHEE therefore supports an independent verification stage.

Example:

Initial implementation
        ↓
Local tests PASS
        ↓
Independent verification FAILS
        ↓
Failure analysis
        ↓
Identify incorrect assumption
        ↓
Generate recovery plan
        ↓
Apply corrected change
        ↓
Run verification again
        ↓
PASS

The recovery system uses the actual failure output as evidence instead of
blindly repeating the previous approach.

Example Recovery

For the included calculator demonstration:

Initial implementation:
divide(10, 0) → 0

Local tests:
PASS

Independent evaluator:
FAIL

Failure:
divide() must raise ValueError for division by zero

Recovery:
Change implementation to raise ValueError

Final local tests:
PASS

Final independent tests:
PASS

This demonstrates why verification and recovery are separate parts of
the harness.

Safety

AI-SHEE does not give unrestricted shell access to the model.

Command execution uses an allowlist of permitted commands and rejects
dangerous commands and shell-control operators.

File operations are also controlled by the tool layer.

Evaluator-owned test directories are protected from modification.

Configuration

AI-SHEE is configured through environment variables.

Repository
export REPOSITORY_PATH=/path/to/repository
Issue
export ISSUE="Fix the authentication bug in the login flow"
Model
export AI_MODE=real
export AI_API_KEY="your-api-key"
export AI_BASE_URL="your-api-base-url"
export AI_MODEL="your-model"

No API keys or secrets are stored in the repository.

Running AI-SHEE
1. Install dependencies
make setup
2. Run
make run
3. Run tests
make test
4. Clean generated files
make clean
Local Development

The repository includes a small calculator project for demonstrating the
agent's investigation, implementation, verification, and recovery loop.

For the local independent-evaluator demonstration:

export AI_MODE=mock
export REPOSITORY_PATH=test_repo
export INDEPENDENT_TEST_PATH=eval_tests

python src/agent.py

A successful run ends with:

=== AI-SHEE SUCCESS ===
Project Structure
ai-shee/
│
├── Makefile
├── README.md
├── requirements.txt
│
├── src/
│   ├── main.py
│   ├── llm.py
│   ├── agent.py
│   ├── tools.py
│   ├── context.py
│   ├── verifier.py
│   ├── recovery.py
│   └── tool_loop.py
│
├── eval_tests/
│   └── test_calculator.py
│
└── test_repo/
    ├── calculator.py
    └── test_calculator.py
Design Principles
Correctness First

A generated change is not considered successful until verification
supports it.

Evidence Over Claims

Test output and tool results are treated as evidence for subsequent
agent decisions.

Recovery Over Repetition

When an approach fails, AI-SHEE analyzes the failure before attempting
another solution.

Focused Context

Relevant repository information is selected instead of blindly sending
the entire repository to the model.

Safe Tool Execution

Commands and file modifications pass through controlled tool interfaces.

Model-Agnostic Architecture

The orchestration layer is separated from the underlying model adapter,
allowing the model configuration to be supplied externally.

Evaluation Interface

AI-SHEE provides the required command interface:

make setup
make run
make test
make clean

The repository and issue can be supplied externally through environment
variables.

The harness is designed so that the underlying model configuration can
also be supplied externally by the evaluation environment.

What Makes AI-SHEE Different

AI-SHEE is built around a simple principle:

A coding agent should not stop when it has generated code.
It should stop when it has evidence that the code works.

The harness therefore treats coding as a closed loop:

Understand
   ↓
Investigate
   ↓
Plan
   ↓
Change
   ↓
Verify
   ↓
Recover if necessary
   ↓
Verify again
   ↓
Finish
