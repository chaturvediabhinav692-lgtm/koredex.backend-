from pathlib import Path
import re


class PatchResult:
    def __init__(self, success, diff, modified_files, new_code, engine):
        self.success = success
        self.diff = diff
        self.modified_files = modified_files
        self.new_code = new_code
        self.engine = engine


class HybridFixEngine:

    def __init__(self, ai_adapter=None):
        self.ai_adapter = ai_adapter

    #  MAIN ENTRY (required by core.py)
    def attempt_fix(self, context):
        return self._deterministic_fix(context)

    # ---------------- RULE ENGINE ---------------- #
    def _deterministic_fix(self, context):

        output = context.output or ""

        # ---------------- ASSERTION DEBUG ---------------- #
        if "AssertionError" in output:
            print("Analyzing assertion failure...")

        # ---------------- TYPE ERROR ---------------- #
        if "TypeError" in output:
            for file in context.failing_files:
                path = Path(file)
                if not path.exists():
                    continue

                code = path.read_text()

                fixed = re.sub(r"(\w+)\s*\+\s*(\w+)", r"int(\1) + int(\2)", code)

                if fixed != code:
                    return PatchResult(
                        success=True,
                        diff="Cast operands to int",
                        modified_files=[str(path)],
                        new_code=fixed,
                        engine="deterministic",
                    )

        # ---------------- ATTRIBUTE ERROR ---------------- #
        if "AttributeError" in output:
            match = re.search(r"'(.+)' object has no attribute '(.+)'", output)

            if match:
                missing = match.group(2)

                for file in context.failing_files:
                    path = Path(file)
                    if not path.exists():
                        continue

                    code = path.read_text()

                    if f"def {missing}" not in code:
                        new_code = code + f"\n\ndef {missing}(self):\n    pass\n"

                        return PatchResult(
                            success=True,
                            diff=f"Added method {missing}",
                            modified_files=[str(path)],
                            new_code=new_code,
                            engine="deterministic",
                        )

        # ---------------- SIMPLE BUG (your old logic) ---------------- #
        for file in context.failing_files:
            path = Path(file)
            if not path.exists():
                continue

            code = path.read_text()

            if "return a - b" in code:
                new_code = code.replace("return a - b", "return a + b")

                return PatchResult(
                    success=True,
                    diff="Fixed arithmetic error",
                    modified_files=[str(path)],
                    new_code=new_code,
                    engine="deterministic",
                )

        return None


# ---------------- ENVIRONMENT FIX ---------------- #

def apply_fix(project_path: str, error_type: str, output: str) -> bool:
    import re
    import subprocess

    if error_type == "IMPORT_ERROR":
        match = re.search(r"No module named '([^']+)'", output)
        if match:
            module = match.group(1)
            print(f"Installing missing module: {module}")
            subprocess.run(["pip", "install", module])
            return True

    return False