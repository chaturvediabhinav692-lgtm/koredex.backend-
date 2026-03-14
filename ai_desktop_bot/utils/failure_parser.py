import re


def extract_failure_file(pytest_output: str):
    """
    Extract the most relevant file from pytest traceback
    """

    lines = pytest_output.splitlines()

    for line in lines:
        # Match: File "path/to/file.py", line X
        match = re.search(r'File "(.+\.py)"', line)
        if match:
            file_path = match.group(1)

            # Ignore test files (optional but recommended)
            if "test_" not in file_path:
                return file_path

    return None