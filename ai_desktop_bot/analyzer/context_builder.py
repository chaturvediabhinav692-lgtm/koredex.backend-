from ai_desktop_bot.analyzer.failure_parser import (
    extract_failure_location,
    extract_expected_actual,
)


def build_debug_context(output: str):
    """
    Build a structured debug context from pytest output.
    """

    file_path, line_number = extract_failure_location(output)

    expected_actual = extract_expected_actual(output)

    context = {
        "file": file_path,
        "line": line_number,
        "error_type": "TEST_FAILURE",
        "assertion": None,
        "expected_actual": expected_actual,
        "code": "",
        "output": output,
    }

    return context