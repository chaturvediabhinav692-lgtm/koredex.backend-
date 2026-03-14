import subprocess
import sys


def run_tests(project_path: str):
    """
    Execute pytest in a fresh Python interpreter so patched modules reload.
    """

    print("RUN_TESTS CALLED")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-vv", "--tb=long"],
        cwd=project_path,
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    return {
        "success": result.returncode == 0,
        "return_code": result.returncode,
        "output": output
    }