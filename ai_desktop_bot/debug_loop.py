import subprocess
import os


def extract_failure_file(output):
    """
    Extract the first Python file path from pytest traceback.
    """

    for line in output.splitlines():

        if ".py:" in line:

            path = line.split(".py:")[0] + ".py"

            if os.path.exists(path):
                return path

    return None


def load_file_code(path):
    """
    Load source code from the failing file.
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    except Exception:
        return ""


class DebugLoop:

    def __init__(self, project_path, max_iterations=3):

        self.project_path = project_path
        self.max_iterations = max_iterations

    def run_tests(self):

        print("RUN_TESTS CALLED")

        try:

            result = subprocess.run(
                [
                    "pytest",
                    self.project_path,
                    "-p",
                    "no:cacheprovider",
                ],
                capture_output=True,
                text=True,
            )

            output = result.stdout + "\n" + result.stderr

            print("RAW RESULT:", {"return_code": result.returncode})

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "output": output,
            }

        except Exception as e:

            print("RUNNER ERROR:", e)

            return {
                "success": False,
                "return_code": -1,
                "output": str(e),
            }

    def count_failures(self, output):

        failed = output.count("FAILED")
        errors = output.count("ERROR")

        return failed + errors

    def build_debug_context(self, output):

        failure_file = extract_failure_file(output)

        code = ""

        if failure_file:
            code = load_file_code(failure_file)

        context = {
            "file": failure_file,
            "line": None,
            "error_type": "TEST_FAILURE",
            "assertion": "assert add(2, 3) == 5",
            "expected_actual": {
                "left": "add(2, 3)",
                "right": "5",
            },
            "code": code,
            "output": output,
        }

        print("\n[DEBUG CONTEXT]")
        print(context)

        return context

    def run(self):

        print(f"\nRunning tests for: {os.path.basename(self.project_path)}\n")

        for i in range(1, self.max_iterations + 1):

            print(f"--- Iteration {i} ---")

            result = self.run_tests()

            output = result["output"]

            context = self.build_debug_context(output)

            failures = self.count_failures(output)

            print(f"Failures: {failures}")

            if failures == 0 and "ERROR" not in output:

                print("\nAll tests passing\n")

                return {
                    "task_complete": True,
                    "final_errors": 0,
                    "iterations": i,
                }

            print("Some tests failing")

        return {
            "task_complete": False,
            "final_errors": failures,
            "iterations": self.max_iterations,
        }


def debug_loop(project_path):
    """
    Entry point used by api.py
    """

    loop = DebugLoop(project_path)

    return loop.run()