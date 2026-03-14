from pathlib import Path
import subprocess
import re
import os

# Optional Gemini import (won't break engine if it fails)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


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

    def attempt_fix(self, context):

        # Try deterministic fix first
        deterministic = self._deterministic_fix(context)
        if deterministic:
            return deterministic

        # Fallback to LLM
        return self._llm_fix(context)

    # -------------------------
    # Deterministic bug fixes
    # -------------------------

    def _deterministic_fix(self, context):

        failing_files = context.get("failing_files", [])

        for file in failing_files:

            path = Path(file)

            if not path.exists():
                continue

            try:
                code = path.read_text(encoding="utf-8")
            except Exception:
                continue

            # Arithmetic subtraction bug
            if "a - b" in code:

                new_code = code.replace("a - b", "a + b")

                return PatchResult(
                    success=True,
                    diff="Fixed subtraction bug",
                    modified_files=[str(path)],
                    new_code=new_code,
                    engine="deterministic",
                )

            # Wrong equality operator
            if "==" in code and "!=" not in code:

                # very basic fallback example
                new_code = code.replace("==", "!=")

                return PatchResult(
                    success=True,
                    diff="Attempted equality logic fix",
                    modified_files=[str(path)],
                    new_code=new_code,
                    engine="deterministic",
                )

        return None

    # -------------------------
    # LLM Fix (Gemini)
    # -------------------------

    def _llm_fix(self, context):

        if not GEMINI_AVAILABLE:
            print("Gemini not available")
            return None

        try:

            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
You are an automated Python bug fixing engine.

The following pytest failure occurred.

Fix the bug in the code.

Only return corrected code.

Failing code:
{context.get("code")}

Expected value: {context.get("expected_actual", {}).get("expected")}
Actual value: {context.get("expected_actual", {}).get("actual")}
"""

            response = model.generate_content(prompt)

            new_code = response.text.strip()

            failing_files = context.get("failing_files", [])

            if not failing_files:
                return None

            return PatchResult(
                success=True,
                diff="LLM generated fix",
                modified_files=failing_files,
                new_code=new_code,
                engine="gemini",
            )

        except Exception as e:

            print("Gemini error:", e)
            return None


# ----------------------------------
# ENVIRONMENT FIX (Dependency errors)
# ----------------------------------

def apply_fix(project_path: str, error_type: str, output: str) -> bool:

    if error_type == "IMPORT_ERROR":

        match = re.search(r"No module named '([^']+)'", output)

        if match:
            module = match.group(1)

            print(f"Installing missing dependency: {module}")

            subprocess.run(["pip", "install", module])

            return True

    return False