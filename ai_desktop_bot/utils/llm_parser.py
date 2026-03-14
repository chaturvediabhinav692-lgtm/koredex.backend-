import re


def clean_output(text: str) -> str:
    # Remove markdown code blocks (```python ... ```)
    text = re.sub(r"```[\w]*\n", "", text)
    text = text.replace("```", "")

    return text.strip()


def has_explanations(text: str) -> bool:
    triggers = [
        "here is", "fix:", "solution:", "updated", "changed",
        "i have", "you can", "this will",
        "the issue", "the problem", "we need to"
    ]

    lower = text.lower()
    return any(t in lower for t in triggers)


def detect_format(text: str) -> str:
    # Unified diff detection
    if text.startswith("---") and "+++" in text and "@@" in text:
        return "diff"

    # Full python file detection
    if "def " in text or "class " in text:
        return "full"

    return "invalid"


def is_single_file_diff(text: str) -> bool:
    return text.count("---") == 1 and text.count("+++") == 1


def is_valid_python(code: str) -> bool:
    try:
        compile(code, "<string>", "exec")
        return True
    except Exception:
        return False


def parse_llm_output(raw_output: str):
    if not raw_output:
        return None, "empty"

    # Reject markdown early (strict mode)
    if "```" in raw_output:
        return None, "markdown_detected"

    cleaned = clean_output(raw_output)

    if not cleaned:
        return None, "empty"

    if has_explanations(cleaned):
        return None, "explanation_detected"

    fmt = detect_format(cleaned)

    if fmt == "invalid":
        return None, "invalid_format"

    if fmt == "diff":
        if not is_single_file_diff(cleaned):
            return None, "multiple_files"

    if fmt == "full":
        if not is_valid_python(cleaned):
            return None, "syntax_error"

    return {
        "type": fmt,
        "content": cleaned
    }, None