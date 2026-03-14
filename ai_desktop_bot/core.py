import os

from ai_desktop_bot.runner import run_tests
from ai_desktop_bot.analyzer import extract_failure_location
from ai_desktop_bot.fix_engine import HybridFixEngine


def debug_loop(project_path: str, max_iterations: int = 5):

    print("DEBUG LOOP STARTED")
    print("\nRunning tests for:", project_path)

    fix_engine = HybridFixEngine()

    failures_found = 0
    failures_fixed = 0
    modified_files = set()

    def extract_relevant_error(output: str):

        lines = output.splitlines()
        error_lines = []
        capture = False

        for line in lines:

            if (
                "Traceback" in line
                or "Error" in line
                or "Exception" in line
                or "FAILED" in line
                or "AssertionError" in line
            ):
                capture = True

            if capture:
                error_lines.append(line)

            if len(error_lines) > 40:
                break

        return "\n".join(error_lines) if error_lines else output[:500]

    for iteration in range(max_iterations):

        print(f"\n--- Iteration {iteration + 1} ---")

        result = run_tests(project_path)

        print("RAW RESULT:", result)

        return_code = result.get("return_code")
        output = result.get("output") or ""

        trimmed_output = extract_relevant_error(output)

        print("\n[TRIMMED ERROR OUTPUT]\n")
        print(trimmed_output)

        if return_code == 0:

            print("\nAll tests passing")

            return {
                "task_complete": True,
                "failures_found": failures_found,
                "failures_fixed": failures_fixed,
                "files_modified": list(modified_files),
                "iterations": iteration + 1
            }

        failures_found += 1

        failure = extract_failure_location(output)

        if not failure:
            import re
            match = re.search(r"([\w/\\]+\.py):(\d+)", output)

            if match:
                failure = {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "error_type": "TEST_FAILURE",
                    "assertion": None,
                    "expected_actual": None
                }

        if not failure:
            print("Analyzer failed to detect failure location")
            break

        file_path = failure.get("file")
        line = failure.get("line")

        if file_path:
            file_path = os.path.join(project_path, file_path)

        code = ""

        if file_path and os.path.exists(file_path):

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                print("Could not read file:", e)

        context = {

            "file": file_path,
            "line": line,
            "error_type": failure.get("error_type"),
            "assertion": failure.get("assertion"),
            "expected_actual": failure.get("expected_actual"),
            "code": code,
            "output": output,
            "failing_files": [file_path] if file_path else []
        }

        print("\nDEBUG CONTEXT:", context)

        patch = fix_engine.attempt_fix(context)

        if not patch:
            print("No fix applied, stopping loop")
            break

        print("\nPatch generated:", patch.diff)

        if patch.new_code and file_path:

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(patch.new_code)

                failures_fixed += 1
                modified_files.add(file_path)

            except Exception as e:
                print("Failed to write patch:", e)
                break

        print("Patch applied")

    return {
        "task_complete": False,
        "failures_found": failures_found,
        "failures_fixed": failures_fixed,
        "files_modified": list(modified_files),
        "iterations": iteration + 1
    }