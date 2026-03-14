import os
import time

from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def generate_fix(code: str, error_output: str):
    prompt = f"""
You are a strict code repair system.

Fix the following Python code so that pytest errors are resolved.

RULES:
- Return ONLY valid unified diff OR full corrected file
- NO explanation
- NO markdown
- NO comments outside code

--- CODE ---
{code}

--- ERRORS ---
{error_output}
"""

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            return response.text

        except Exception as e:
            error_str = str(e)

            # -------- RATE LIMIT HANDLING -------- #
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                wait_time = RETRY_DELAY * (attempt + 1)
                print(f"[LLM] Rate limited. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            # -------- OTHER ERRORS -------- #
            print(f"[LLM ERROR] {e}")
            return None

    print("[LLM] Max retries exceeded")
    return None