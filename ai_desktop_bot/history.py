import hashlib

applied_fixes = set()


def hash_fix(file_path: str, content: str) -> str:
    return hashlib.md5((file_path + content).encode()).hexdigest()


def is_duplicate_fix(file_path: str, content: str) -> bool:
    h = hash_fix(file_path, content)
    return h in applied_fixes


def register_fix(file_path: str, content: str):
    h = hash_fix(file_path, content)
    applied_fixes.add(h)