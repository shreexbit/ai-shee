import os
import shutil
import subprocess
import sys
from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "coverage",
}


IGNORED_FILE_SUFFIXES = {
    ".ai-shee-backup",
}


PROTECTED_DIRECTORIES = {
    "eval_tests",
}


# Commands that an autonomous coding agent is allowed
# to execute during repository investigation.
ALLOWED_COMMANDS = {
    "python",
    "python3",
    "pytest",
    "pip",
    "pip3",
    "node",
    "npm",
    "npx",
    "git",
    "ls",
    "pwd",
    "cat",
    "grep",
    "find",
    "head",
    "tail",
    "wc",
}


# Clearly destructive commands that should never be
# executed by the autonomous agent.
BLOCKED_COMMANDS = {
    "rm",
    "rmdir",
    "sudo",
    "shutdown",
    "reboot",
    "mkfs",
    "format",
    "kill",
    "killall",
}


def should_ignore_file(filename):

    for suffix in IGNORED_FILE_SUFFIXES:

        if filename.endswith(suffix):
            return True

    return False


def list_files(path="."):

    files = []

    for root, dirs, filenames in os.walk(path):

        dirs[:] = [
            directory
            for directory in dirs
            if directory not in IGNORED_DIRECTORIES
        ]

        for filename in filenames:

            if should_ignore_file(filename):
                continue

            files.append(
                os.path.join(
                    root,
                    filename
                )
            )

    return files


def build_repository_map(path="."):

    files = list_files(path)

    python_files = []
    javascript_files = []
    typescript_files = []
    test_files = []
    config_files = []
    documentation_files = []
    other_files = []

    for file_path in files:

        filename = os.path.basename(
            file_path
        )

        lower_name = filename.lower()

        if (
            lower_name.startswith("test_")
            or lower_name.endswith("_test.py")
            or "/tests/" in file_path
            or "\\tests\\" in file_path
        ):

            test_files.append(
                file_path
            )

        elif lower_name.endswith(".py"):

            python_files.append(
                file_path
            )

        elif lower_name.endswith(".js"):

            javascript_files.append(
                file_path
            )

        elif lower_name.endswith(".ts"):

            typescript_files.append(
                file_path
            )

        elif lower_name in {
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "makefile",
            "dockerfile",
            ".env.example",
        }:

            config_files.append(
                file_path
            )

        elif lower_name.endswith(
            (
                ".md",
                ".txt",
                ".rst"
            )
        ):

            documentation_files.append(
                file_path
            )

        else:

            other_files.append(
                file_path
            )

    if python_files:

        project_type = "Python"

    elif javascript_files or typescript_files:

        project_type = "JavaScript/TypeScript"

    else:

        project_type = "Unknown"

    return {
        "project_type": project_type,
        "total_files": len(files),
        "python_files": python_files,
        "javascript_files": javascript_files,
        "typescript_files": typescript_files,
        "test_files": test_files,
        "config_files": config_files,
        "documentation_files": documentation_files,
        "other_files": other_files,
    }


def search_code(query, path="."):

    matches = []

    query_lower = query.lower()

    for root, dirs, filenames in os.walk(path):

        dirs[:] = [
            directory
            for directory in dirs
            if directory not in IGNORED_DIRECTORIES
        ]

        for filename in filenames:

            if should_ignore_file(filename):
                continue

            file_path = os.path.join(
                root,
                filename
            )

            filename_lower = filename.lower()

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as file:

                    for line_number, line in enumerate(
                        file,
                        start=1
                    ):

                        line_lower = line.lower()

                        if query_lower not in line_lower:
                            continue

                        score = 0

                        if query_lower in filename_lower:
                            score += 50

                        if query_lower in line_lower:
                            score += 20

                        if filename_lower.endswith(
                            (
                                ".py",
                                ".js",
                                ".ts"
                            )
                        ):

                            score += 10

                        if (
                            filename_lower.startswith("test_")
                            or "test" in filename_lower
                        ):

                            score -= 5

                        matches.append({
                            "file": file_path,
                            "line": line_number,
                            "content": line.strip(),
                            "score": score
                        })

            except (
                UnicodeDecodeError,
                PermissionError
            ):

                continue

    matches.sort(
        key=lambda result: result["score"],
        reverse=True
    )

    # Keep only the strongest matches so repeated searches
    # do not flood the model context.
    return matches[:20]


def read_file(
    path,
    start_line=1,
    end_line=None
):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        lines = file.readlines()

    if end_line is None:

        end_line = len(lines)

    selected_lines = lines[
        start_line - 1:end_line
    ]

    result = []

    for line_number, line in enumerate(
        selected_lines,
        start=start_line
    ):

        result.append(
            f"{line_number} | {line.rstrip()}"
        )

    return "\n".join(result)


def edit_file(
    path,
    new_content,
    repository_path
):

    normalized_path = os.path.normpath(
        path
    )

    if (
        normalized_path == "eval_tests"
        or normalized_path.startswith(
            "eval_tests" + os.sep
        )
    ):

        return {
            "success": False,
            "file": path,
            "message": (
                "Edit blocked: "
                "protected evaluation file"
            )
        }

    repository_root = os.path.abspath(
        repository_path
    )

    target_path = os.path.abspath(
        path
    )

    try:

        common_path = os.path.commonpath([
            repository_root,
            target_path
        ])

    except ValueError:

        return {
            "success": False,
            "file": path,
            "message": "Invalid file path"
        }

    if common_path != repository_root:

        return {
            "success": False,
            "file": path,
            "message": (
                "Edit blocked: "
                "file is outside repository"
            )
        }

    backup_path = (
        target_path
        + ".ai-shee-backup"
    )

    try:

        if os.path.exists(target_path):

            shutil.copy2(
                target_path,
                backup_path
            )

        parent_directory = os.path.dirname(
            target_path
        )

        os.makedirs(
            parent_directory,
            exist_ok=True
        )

        with open(
            target_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                new_content
            )

        return {
            "success": True,
            "file": path,
            "backup": backup_path,
            "message": (
                "File updated successfully"
            )
        }

    except Exception as error:

        return {
            "success": False,
            "file": path,
            "message": str(error)
        }


def replace_text(
    path,
    old_text,
    new_text,
    repository_path
):

    normalized_path = os.path.normpath(
        path
    )

    repository_root = os.path.abspath(
        repository_path
    )

    if os.path.isabs(normalized_path):

        target_path = os.path.abspath(
            normalized_path
        )

    else:

        target_path = os.path.abspath(
            os.path.join(
                repository_root,
                normalized_path
            )
        )

    try:

        relative_path = os.path.relpath(
            target_path,
            repository_root
        )

    except ValueError:

        return {
            "success": False,
            "file": path,
            "message": "Invalid file path"
        }

    if (
        relative_path == "eval_tests"
        or relative_path.startswith(
            "eval_tests" + os.sep
        )
    ):

        return {
            "success": False,
            "file": path,
            "message": (
                "Edit blocked: "
                "protected evaluation file"
            )
        }

    try:

        common_path = os.path.commonpath(
            [repository_root, target_path]
        )

    except ValueError:

        return {
            "success": False,
            "file": path,
            "message": "Edit blocked: invalid path"
        }

    if common_path != repository_root:

        return {
            "success": False,
            "file": path,
            "message": (
                "Edit blocked: "
                "file is outside repository"
            )
        }

    if not os.path.isfile(target_path):

        return {
            "success": False,
            "file": path,
            "message": "File does not exist"
        }

    content = Path(target_path).read_text()

    occurrences = content.count(
        old_text
    )

    if occurrences == 0:

        return {
            "success": False,
            "file": path,
            "message": (
                "Replacement text was not found"
            )
        }

    if occurrences > 1:

        return {
            "success": False,
            "file": path,
            "message": (
                "Replacement text is ambiguous: "
                f"found {occurrences} matches"
            )
        }

    backup_path = (
        target_path + ".ai-shee-backup"
    )

    shutil.copy2(
        target_path,
        backup_path
    )

    updated_content = content.replace(
        old_text,
        new_text,
        1
    )

    Path(target_path).write_text(
        updated_content
    )

    return {
        "success": True,
        "file": path,
        "message": "Text replacement applied",
        "backup": backup_path
    }


def restore_file(path):

    backup_path = (
        path
        + ".ai-shee-backup"
    )

    if not os.path.exists(
        backup_path
    ):

        return {
            "success": False,
            "message": "No backup found"
        }

    try:

        shutil.copy2(
            backup_path,
            path
        )

        return {
            "success": True,
            "message": (
                "File restored successfully"
            )
        }

    except Exception as error:

        return {
            "success": False,
            "message": str(error)
        }


def run_command(
    command,
    repository_path,
    timeout=30
):

    # ----------------------------------------------
    # BASIC COMMAND VALIDATION
    # ----------------------------------------------

    if not command or not command.strip():

        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": "Empty command rejected.",
            "command": command
        }

    command_parts = command.strip().split()

    base_command = os.path.basename(
        command_parts[0]
    )

    # ----------------------------------------------
    # BLOCK OBVIOUSLY DANGEROUS COMMANDS
    # ----------------------------------------------

    for part in command_parts:

        normalized_part = os.path.basename(
            part
        )

        if normalized_part in BLOCKED_COMMANDS:

            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": (
                    f"Command blocked by safety policy: "
                    f"{normalized_part}"
                ),
                "command": command
            }

    # ----------------------------------------------
    # ALLOW ONLY KNOWN COMMANDS
    # ----------------------------------------------

    if base_command not in ALLOWED_COMMANDS:

        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": (
                f"Command not allowed: "
                f"{base_command}"
            ),
            "command": command
        }

    # ----------------------------------------------
    # BLOCK COMMON SHELL CONTROL OPERATORS
    # ----------------------------------------------

    dangerous_tokens = {
        ";",
        "&&",
        "||",
        "|",
        ">",
        ">>",
        "<",
        "`",
        "$(",
    }

    for token in dangerous_tokens:

        if token in command:

            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": (
                    "Shell control operator blocked: "
                    f"{token}"
                ),
                "command": command
            }

    # ----------------------------------------------
    # EXECUTE
    # ----------------------------------------------
    if command.strip() == "pytest":
        command = f'"{sys.executable}" -m pytest'

    try:

        result = subprocess.run(
            command,
            cwd=repository_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        def compact_output(output, head=4000, tail=2000):
            if not output:
                return ""

            limit = head + tail

            if len(output) <= limit:
                return output

            return (
                output[:head]
                + "\n\n... [OUTPUT TRUNCATED FOR CONTEXT EFFICIENCY] ...\n\n"
                + output[-tail:]
            )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": compact_output(result.stdout),
            "stderr": compact_output(result.stderr),
            "command": command
        }

    except subprocess.TimeoutExpired:

        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": (
                f"Command timed out "
                f"after {timeout} seconds"
            ),
            "command": command
        }

    except Exception as error:

        return {
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": str(error),
            "command": command
        }
