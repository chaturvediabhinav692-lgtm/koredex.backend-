import re


def extract_failure_location(output: str):
    """
    Extract the most relevant failing source file and line number
    from pytest output.

    Returns dictionary:
    {
        "file": str,
        "line": int,
        "error_type": str,
        "assertion": None,
        "expected_actual": dict | None
    }
    """

    # match file paths like:
    # calculator.py:3
    # test_repo/test_sample.py:5
    pattern = r"([A-Za-z0-9_\\\/\.\-]+\.py):(\d+)"

    matches = re.findall(pattern, output)

    if not matches:
        return None

    # prefer non-test source files
    for file_path, line in reversed(matches):

        filename = file_path.lower()

        if not filename.startswith("test_") and "/test_" not in filename and "\\test_" not in filename:
            return {
                "file": file_path,
                "line": int(line),
                "error_type": "ASSERTION_FAILURE",
                "assertion": None,
                "expected_actual": extract_expected_actual(output)
            }

    # fallback if only test files found
    file_path, line = matches[-1]

    return {
        "file": file_path,
        "line": int(line),
        "error_type": "ASSERTION_FAILURE",
        "assertion": None,
        "expected_actual": extract_expected_actual(output)
    }


def extract_expected_actual(output: str):
    """
    Extract expected vs actual values from pytest assertion output.

    Example line:
        E assert -1 == 5
    """

    pattern = r"E\s+assert\s+(.+?)\s*==\s*(.+)"

    match = re.search(pattern, output)

    if match:
        actual = match.group(1).strip()
        expected = match.group(2).strip()

        return {
            "actual": actual,
            "expected": expected
        }

    return None