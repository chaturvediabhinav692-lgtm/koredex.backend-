from fastapi import FastAPI, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase_client import supabase
from dotenv import load_dotenv

import os
import sys
import signal
import tempfile
import shutil
import zipfile
import uuid

from ai_desktop_bot.core import debug_loop


# ================= LOAD ENV =================

load_dotenv()

print("Gemini key loaded:", bool(os.getenv("GEMINI_API_KEY")), flush=True)

app = FastAPI(
    title="Koredex Backend",
    version="1.0"
)


# ================= HEALTH CHECK =================

@app.get("/")
def health():
    return {"status": "backend running"}


# ================= ENABLE CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= SECURITY: DANGEROUS CODE CHECK =================

def check_dangerous_code(repo_path: str):

    dangerous_patterns = [
        "os.system",
        "rm -rf",
        "shutil.rmtree",
        "subprocess.call",
        "eval(",
        "exec("
    ]

    for root, dirs, files in os.walk(repo_path):

        for file in files:

            if file.endswith(".py"):

                filepath = os.path.join(root, file)

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()

                    for pattern in dangerous_patterns:
                        if pattern in content:
                            return False, f"Unsafe pattern detected: {pattern}"

                except Exception:
                    pass

    return True, "safe"


# ================= SECURITY: TIMEOUT =================

def timeout_handler(signum, frame):
    raise TimeoutError("Run exceeded 60 seconds")


# ================= RUN ENDPOINT =================

@app.post("/run")
async def run_repo(file: UploadFile = File(...), authorization: str = Header(None)):

    request_id = str(uuid.uuid4())[:8]

    print(f"[{request_id}] RUN ENDPOINT HIT", flush=True)

    result = {}

    # ================= AUTH =================

    if not authorization:
        print(f"[{request_id}] Missing Authorization header", flush=True)
        return {"error": "Missing token"}

    if authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    else:
        token = authorization

    try:

        print(f"[{request_id}] Verifying Supabase token", flush=True)

        user_response = supabase.auth.get_user(token)

        user = user_response.user

        if not user:
            print(f"[{request_id}] Token valid but user missing", flush=True)
            return {"error": "Invalid user"}

        user_id = user.id

        print(f"[{request_id}] Authenticated user:", user_id, flush=True)

    except Exception as e:

        print(f"[{request_id}] Auth failure:", str(e), flush=True)
        return {"error": "Invalid token"}

    # ================= FETCH USER =================

    try:

        db_response = supabase.table("users").select("*").eq("id", user_id).execute()

        if not db_response.data:
            print(f"[{request_id}] User not found in DB", flush=True)
            return {"error": "User not found"}

        user_data = db_response.data[0]

        print(f"[{request_id}] DB user record:", user_data, flush=True)

    except Exception as e:

        print(f"[{request_id}] DB lookup failed:", str(e), flush=True)
        return {"error": "Database error"}

    # ================= LIMIT CHECK =================

    if user_data["runs_used"] >= user_data["runs_limit"]:

        print(f"[{request_id}] Usage limit reached", flush=True)

        return {"error": "Limit reached"}

    # ================= RUN BOT =================

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            print(f"[{request_id}] Temp dir:", temp_dir, flush=True)

            zip_path = os.path.join(temp_dir, file.filename)

            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            print(f"[{request_id}] Zip saved:", zip_path, flush=True)

            extract_path = os.path.join(temp_dir, "repo")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            print(f"[{request_id}] Repo extracted:", extract_path, flush=True)

            # ================= SECURITY CHECK =================

            is_safe, reason = check_dangerous_code(extract_path)

            if not is_safe:

                print(f"[{request_id}] Unsafe repo:", reason, flush=True)

                return {
                    "task_complete": False,
                    "error": reason
                }

            print(f"[{request_id}] Security check passed", flush=True)

            # ================= TIMEOUT =================

            use_timeout = sys.platform != "win32"

            if use_timeout:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)

            print(f"[{request_id}] Starting debug_loop", flush=True)

            try:

                result = debug_loop(extract_path)

                if use_timeout:
                    signal.alarm(0)

            except TimeoutError:

                print(f"[{request_id}] Execution timeout", flush=True)

                return {
                    "task_complete": False,
                    "error": "Run exceeded 60 seconds"
                }

            print(f"[{request_id}] debug_loop result:", result, flush=True)

    except Exception as e:

        print(f"[{request_id}] Execution error:", str(e), flush=True)

        return {
            "task_complete": False,
            "error": str(e)
        }

    # ================= INCREMENT USAGE =================

    try:

        supabase.table("users").update({
            "runs_used": user_data["runs_used"] + 1
        }).eq("id", user_id).execute()

        print(f"[{request_id}] Usage incremented", flush=True)

    except Exception as e:

        print(f"[{request_id}] Usage update failed:", str(e), flush=True)

    # ================= FINAL RESPONSE =================

    response_data = {
        "task_complete": result.get("task_complete", False),
        "failures_found": result.get("failures_found", 0),
        "failures_fixed": result.get("failures_fixed", 0),
        "files_modified": result.get("files_modified", []),
        "iterations": result.get("iterations", 0)
    }

    print(f"[{request_id}] Returning response:", response_data, flush=True)

    return response_data


# ================= LOCAL RUN =================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port
    )