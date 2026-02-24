from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()  # Load values from .env

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase credentials are missing. Check your .env file.")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


# ------------------------------------------------------------
# Create ONE global supabase client for the entire application
# ------------------------------------------------------------
supabase: Client = get_supabase()