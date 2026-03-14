def get_code_context(file_path, line, window=20):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        start = max(0, line - window)
        end = min(len(lines), line + window)

        return "".join(lines[start:end])
    except Exception:
        return ""