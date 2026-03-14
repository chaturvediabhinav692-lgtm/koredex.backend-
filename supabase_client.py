from supabase import create_client
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("Loaded URL:", SUPABASE_URL)  # debug
print("Loaded KEY prefix:", SUPABASE_KEY[:10] if SUPABASE_KEY else None)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)