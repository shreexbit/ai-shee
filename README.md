Absolutely 😭 — the content is good, but the README should **look like a real hackathon project**, not a technical dump.

Copy this version directly:

# 🧠 AI-SHEE

### Autonomous Coding Harness

> **Don't stop when code is generated. Stop when there is evidence that it works.**

AI-SHEE is an autonomous coding-agent harness that combines **repository intelligence, tool use, context management, verification, and failure recovery** to solve software engineering tasks.

---

## ⚡ What AI-SHEE Does

```text
                    ┌──────────────┐
                    │    ISSUE     │
                    └──────┬───────┘
                           ↓
                  ┌─────────────────┐
                  │  TASK ANALYSIS  │
                  └────────┬────────┘
                           ↓
              ┌─────────────────────────┐
              │ REPOSITORY INTELLIGENCE │
              │  Map + Search + Context │
              └────────────┬────────────┘
                           ↓
                    ┌─────────────┐
                    │  TOOL LOOP  │
                    │ Search/Read │
                    │    /Run     │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │ CODE PLANNER│
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │ APPLY CHANGE│
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │ VERIFICATION│
                    └──────┬──────┘
                           ↓
                     ┌─────┴─────┐
                     │           │
                   PASS         FAIL
                     │           │
                     ↓           ↓
                   DONE      ┌──────────┐
                             │ RECOVERY │
                             │ ANALYSIS │
                             └────┬─────┘
                                  ↓
                           FRESH CONTEXT
                                  ↓
                           RECOVERY PLAN
                                  ↓
                              VERIFY
```

---

## 🚀 Key Capabilities

### 🔍 Repository Intelligence

AI-SHEE builds a lightweight repository map and searches for relevant
code instead of blindly passing the entire repository to the model.

### 🛠️ Autonomous Tool Loop

The model can decide when to use:

* `search_code`
* `read_file`
* `run_command`

Tool history is bounded to keep context focused.

### 🧠 Context Management

AI-SHEE tracks:

* Relevant files
* Tool history
* Observations
* Changes
* Test results
* Failed approaches

During recovery, it **re-reads the current repository state** instead of
reusing stale information from the failed attempt.

### 📝 Structured Code Planning

Every planned change contains:

* Target file
* Operation
* Reason
* Replacement or rewritten content

For replacements, `old_text` must come from the **current repository state**.

### ✅ Verification

Code generation is not considered success.

AI-SHEE verifies the resulting software and uses test results as evidence
for subsequent decisions.

### 🔄 Failure Recovery

When verification fails, AI-SHEE analyzes the failure, creates a new plan,
and retries using fresh repository context.

---

# 🧪 Recovery Demonstration

The included calculator project demonstrates the complete recovery loop.

```text
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
Recovery plan
        ↓
Corrected implementation
        ↓
Independent tests PASS
```

### Example

The initial implementation handled:

```text
divide(10, 0) → 0
```

The independent evaluator required:

```text
divide(10, 0) → ValueError
```

AI-SHEE detects the mismatch, analyzes the failure, rebuilds its recovery
context, applies the corrected implementation, and verifies it again.

Successful completion:

```text
✓ Local tests passed
✓ Independent tests passed

=== AI-SHEE SUCCESS ===
```

---

# 🛡️ Safety

AI-SHEE does not give unrestricted shell access to the model.

It provides:

* Controlled command execution
* Dangerous command/operator rejection
* Repository path validation
* Protected evaluator directories
* Exact text replacement
* Backups before modifications

---

# ⚙️ Quick Start

### Install

```bash
make setup
```

### Run

```bash
make run
```

### Test

```bash
make test
```

### Clean

```bash
make clean
```

---

# 🧪 Local Independent Evaluator

For the included deterministic demonstration:

```bash
export AI_MODE=mock
export REPOSITORY_PATH=test_repo
export INDEPENDENT_TEST_PATH=eval_tests

make run
```

> **`INDEPENDENT_TEST_PATH` enables independent verification.**
> Without it, independent verification is skipped.

A successful run ends with:

```text
=== AI-SHEE SUCCESS ===
```

---

# 🔌 Configuration

```bash
export REPOSITORY_PATH=/path/to/repository
export ISSUE="Fix the authentication bug"
export AI_MODE=real
export AI_API_KEY="your-api-key"
export AI_BASE_URL="your-api-base-url"
export AI_MODEL="your-model"
```

**No API keys or secrets are stored in the repository.**

---

# 📦 Project Structure

```text
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
```

---

# 🧩 Design Principles

| Principle                    | Approach                                    |
| ---------------------------- | ------------------------------------------- |
| **Correctness First**        | Code is successful only after verification  |
| **Evidence Over Claims**     | Tool results and tests drive decisions      |
| **Recovery Over Repetition** | Failures trigger analysis before retrying   |
| **Fresh Context**            | Recovery uses the current repository state  |
| **Focused Context**          | Relevant code is prioritized                |
| **Safe Execution**           | Model actions pass through controlled tools |

---

# 🎯 The Core Idea

AI-SHEE treats coding as a **closed-loop engineering process**:

```text
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
```

### **Generate less. Verify more.**
