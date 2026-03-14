import os

BLOCKED_PATHS = [
    "site-packages",
    ".pytest_cache",
    "__pycache__",
    "dist-packages",
]

ALLOWED_ROOTS = [
    "test_project",
    "itsdangerous",
    "markupsafe",
]


def is_safe_path(file_path: str) -> bool:
    file_path = os.path.abspath(file_path)

    for blocked in BLOCKED_PATHS:
        if blocked in file_path:
            return False

    return any(root in file_path for root in ALLOWED_ROOTS)


def assert_safe(file_path: str):
    if not is_safe_path(file_path):
        raise PermissionError(f"Blocked unsafe edit: {file_path}")