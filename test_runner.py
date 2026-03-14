import subprocess
import json

repos = ["itsdangerous", "markupsafe", "click"]
results = []

for repo in repos:
    print("\n" + "=" * 60)
    print(f"Testing repo: {repo}")
    print("=" * 60)

    result = subprocess.run(
        [
            "python",
            "-m",
            "ai_desktop_bot.cli",
            "run tests",
            "--project",
            repo,
            "-y",
        ],
        capture_output=True,
        text=True,
    )

    if not result.stdout.strip():
        print("No output from CLI.")
        results.append((repo, False))
        continue

    lines = result.stdout.strip().splitlines()

    try:
        data = json.loads(lines[-1])

        print("Parsed JSON:", data)

        success = data.get("task_complete", False)

    except Exception as e:
        print("Failed to parse JSON:", e)
        success = False

    results.append((repo, success))


print("\n" + "=" * 60)
print("FINAL REPORT")
print("=" * 60)

success_count = 0

for repo, success in results:
    status = "SUCCESS" if success else "FAILED"
    print(f"{repo:<15} | {status}")
    if success:
        success_count += 1

rate = (success_count / len(results)) * 100

print("=" * 60)
print(f"SUCCESS RATE: {success_count}/{len(results)} = {rate:.2f}%")
print("=" * 60)