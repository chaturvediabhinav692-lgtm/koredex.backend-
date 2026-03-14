def classify_failure(output: str) -> str:
    output_lower = output.lower()

    if "importerror" in output_lower or "module not found" in output_lower:
        return "import"

    if "assertionerror" in output_lower:
        return "assertion"

    if "typeerror" in output_lower:
        return "type"

    if "attributeerror" in output_lower:
        return "attribute"

    if "indentationerror" in output_lower or "syntaxerror" in output_lower:
        return "syntax"

    return "unknown"