from fastapi import FastAPI, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase_client import supabase
from dotenv import load_dotenv
from jose import jwt

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

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

print("Gemini key loaded:", bool(os.getenv("GEMINI_API_KEY")), flush=True)

app = FastAPI(
    title="Koredex Backend",
    version="1.0"
)


# ================= HEALTH =================

@app.get("/")
def health():
    return {"status": "backend running"}


# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= TOKEN VERIFY =================

def verify_token(token: str):

    payload = jwt.decode(
        token,
        SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated"
    )

    return payload["sub"]


# ================= SECURITY: CODE SCAN =================

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


# ================= TIMEOUT =================

def timeout_handler(signum, frame):
    raise TimeoutError("Run exceeded 60 seconds")


# ================= RUN ENDPOINT =================

@app.post("/run")
async def run_repo(file: UploadFile = File(...), authorization: str = Header(None)):

    request_id = str(uuid.uuid4())[:8]

    print(f"[{request_id}] RUN ENDPOINT HIT", flush=True)

    if not authorization:
        return {"error": "Missing token"}

    # clean header
    token = authorization.replace("Bearer", "").strip()

    print(f"[{request_id}] Verifying JWT locally", flush=True)

    try:

        user_id = verify_token(token)

        print(f"[{request_id}] Authenticated user:", user_id, flush=True)

    except Exception as e:

        print(f"[{request_id}] Token verification failed:", str(e), flush=True)

        return {"error": "Invalid token"}

    # ================= FETCH USER =================

    try:

        db_response = supabase.table("users").select("*").eq("id", user_id).execute()

        if not db_response.data:
            return {"error": "User not found"}

        user_data = db_response.data[0]

        print(f"[{request_id}] DB user:", user_data, flush=True)

    except Exception as e:

        print(f"[{request_id}] DB error:", str(e), flush=True)

        return {"error": "Database error"}

    # ================= LIMIT CHECK =================

    if user_data["runs_used"] >= user_data["runs_limit"]:
        return {"error": "Limit reached"}

    result = {}

    # ================= RUN DEBUG ENGINE =================

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            zip_path = os.path.join(temp_dir, file.filename)

            with open(zip_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            extract_path = os.path.join(temp_dir, "repo")

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)

            print(f"[{request_id}] Repo extracted:", extract_path, flush=True)

            is_safe, reason = check_dangerous_code(extract_path)

            if not is_safe:
                return {
                    "task_complete": False,
                    "error": reason
                }

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

    # ================= UPDATE USAGE =================

    try:

        supabase.table("users").update({
            "runs_used": user_data["runs_used"] + 1
        }).eq("id", user_id).execute()

    except Exception as e:

        print(f"[{request_id}] Usage update failed:", str(e), flush=True)

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