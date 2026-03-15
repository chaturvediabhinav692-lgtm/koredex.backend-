from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

print("Loaded URL:", SUPABASE_URL)
print("Loaded KEY prefix:", SUPABASE_KEY[:10])

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)