from ai_desktop_bot.utils.llm_engine import generate_fix
from ai_desktop_bot.utils.llm_parser import parse_llm_output

file_content = """
def add(a, b):
    return a - b
"""

error_output = "Expected 5 but got -1"

fix = generate_fix(file_content, error_output)

print("\n--- RAW OUTPUT ---\n")
print(fix)

parsed, error = parse_llm_output(fix)

print("\n--- PARSED ---\n")
print(parsed)
print("Error:", error)