# ai_desktop_bot/analyzer.py

def analyze_test_output(output: str, return_code: int) -> bool:
    o = output.lower()

    # Strong positive signal: all tests passed
    if "passed" in o and "failed" not in o:
        return True

    # Real failure signals
    failure_signals = [
        "assertionerror",
        "failed",
        "importerror",
        "modulenotfounderror",
    ]

    for signal in failure_signals:
        if signal in o:
            return False

    # fallback
    return return_code == 0


def classify_error(output: str) -> str:
    """
    Classifies pytest output into error categories.
    """

    output_lower = output.lower()

    # 1. Import errors (strict)
    if "modulenotfounderror" in output_lower:
        return "IMPORT_ERROR"

    # 2. Syntax errors
    if "syntaxerror" in output_lower:
        return "SYNTAX_ERROR"

    # 3. Test failures (VERY IMPORTANT)
    if "failed" in output_lower or "assertionerror" in output_lower:
        return "TEST_FAILURE"

    # 4. Runtime errors
    if "traceback" in output_lower:
        return "RUNTIME_ERROR"

    return "UNKNOWN" 

import re
def extract_failure_location(output: str):
    """
    Extract failing file, line, and test name from pytest output
    """
    file_match = re.search(r"([a-zA-Z0-9_/\\]+\.py):(\d+)", output)
    test_match = re.search(r"FAILED\s+([^\s]+)", output)

    file = file_match.group(1) if file_match else None
    line = int(file_match.group(2)) if file_match else None
    test = test_match.group(1) if test_match else None

    return file, line, test 
def extract_assertion_error(output: str):
    """
    Extract assertion error message
    """
    import re

    match = re.search(r"AssertionError:(.*)", output)
    if match:
        return match.group(1).strip()

    return None