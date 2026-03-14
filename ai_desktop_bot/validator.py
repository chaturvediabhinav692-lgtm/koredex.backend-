def is_valid_python(code: str) -> bool:
    """
    Checks if given code is valid Python syntax.
    """
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False