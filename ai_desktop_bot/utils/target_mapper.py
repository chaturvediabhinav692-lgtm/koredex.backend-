import os
import re


def detect_target_file_from_output(output: str, project_path: str):
    match = re.search(r"tests[\\/].*?\.py", output)
    if not match:
        return None

    test_file = match.group(0)

    source_guess = test_file.replace("tests\\", "").replace("tests/", "")
    source_guess = source_guess.replace("test_", "")

    possible_paths = [
        os.path.join(project_path, "src", source_guess),
        os.path.join(project_path, source_guess),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None