import argparse
import json

from ai_desktop_bot.core import debug_loop


def main():
    print("CLI STARTED")  # debug marker

    parser = argparse.ArgumentParser()
    parser.add_argument("instruction")
    parser.add_argument("--project", required=True)
    parser.add_argument("-y", "--yes", action="store_true")

    args = parser.parse_args()

    result = debug_loop(args.project)

    print("\n" + "=" * 60)
    print("RESULT SUMMARY")
    print("=" * 60)

    if result.get("task_complete"):
        print("Status       : SUCCESS")
        print("Final Errors : 0")
    else:
        print("Status       : FAILED")
        print(f"Final Errors : {result.get('final_errors')}")

    print("=" * 60)

    print(json.dumps(result))


if __name__ == "__main__":
    main()