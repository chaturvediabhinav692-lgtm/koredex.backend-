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

from ai_desktop_bot.core import debug_loop


# ================= LOAD ENV =================

load_dotenv()
print("Gemini key loaded:", bool(os.getenv("GEMINI_API_KEY")))

app = FastAPI(
    title="Koredex AI Debugger",
    version="1.0"
)

# ================= HEALTH CHECK =================

@app.get("/")
def health():
    return {"status": "koredex backend running"}


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

    # ================= AUTH =================

    if not authorization:
        return {"error": "Missing token"}

    token = authorization.replace("Bearer ", "")

    try:
        user_response = supabase.auth.get_user(token)
        user_id = user_response.user.id
    except Exception:
        return {"error": "Invalid token"}

    print("Authenticated user:", user_id)

    # ================= FETCH USER =================

    db_response = supabase.table("users").select("*").eq("id", user_id).execute()

    if not db_response.data:
        return {"error": "User not found"}

    user_data = db_response.data[0]
    print("Database response:", user_data)

    # ================= LIMIT CHECK =================

    if user_data["runs_used"] >= user_data["runs_limit"]:
        return {"error": "Limit reached"}

    # ================= RUN BOT =================

    try:
        with tempfile.TemporaryDirectory() as temp_dir:

            filename = file.filename or "repo.zip"
            zip_path = os.path.join(temp_dir, filename)

            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            extract_path = os.path.join(temp_dir, "repo")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            # ================= SECURITY CHECK =================

            is_safe, reason = check_dangerous_code(extract_path)

            if not is_safe:
                return {
                    "task_complete": False,
                    "error": reason
                }

            # ================= TIMEOUT =================

            use_timeout = sys.platform != "win32"

            if use_timeout:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(60)

            try:
                result = debug_loop(extract_path)

                if use_timeout:
                    signal.alarm(0)

            except TimeoutError:
                return {
                    "task_complete": False,
                    "error": "Run exceeded 60 seconds"
                }

    except Exception as e:
        return {
            "task_complete": False,
            "error": str(e)
        }

    # ================= DEBUG LOG =================

    print("FINAL RESULT:", result)

    # ================= INCREMENT USAGE =================

    try:
        supabase.table("users").update({
            "runs_used": user_data["runs_used"] + 1
        }).eq("id", user_id).execute()
    except Exception as e:
        print("Usage update failed:", e)

    # ================= CORRECT RESPONSE FORMAT =================

    return {
        "task_complete": result.get("task_complete", False),
        "failures_found": result.get("failures_found", 0),
        "failures_fixed": result.get("failures_fixed", 0),
        "files_modified": result.get("files_modified", []),
        "iterations": result.get("iterations", 0)
    }


# ================= SERVER START =================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port
    )