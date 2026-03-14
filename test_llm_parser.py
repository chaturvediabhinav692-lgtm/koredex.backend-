from ai_desktop_bot.utils.llm_parser import parse_llm_output


cases = [
    "Here is the fix:\nreturn a + b",
    "```python\ndef add(a,b): return a+b\n```",
    "--- a.py\n+++ a.py\n@@\n- return a-b\n+ return a+b",
    "def add(a, b): return a + b",
    ""
]

for i, case in enumerate(cases, 1):
    result, err = parse_llm_output(case)
    print(f"\nTest {i}")
    print("Result:", result)
    print("Error:", err)