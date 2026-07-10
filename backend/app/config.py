"""Central configuration, read once from environment / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'rfq_copilot.db'}"
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

DEFAULT_GST_RATE = float(os.getenv("DEFAULT_GST_RATE", "0.28"))
FREIGHT_ESTIMATE_PER_BAG = float(os.getenv("FREIGHT_ESTIMATE_PER_BAG", "10"))
FREIGHT_ESTIMATE_PER_TONNE = float(os.getenv("FREIGHT_ESTIMATE_PER_TONNE", "200"))

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# GST rates by product family — used when a vendor says "GST extra"
GST_RATES = {"cement": 0.28, "steel": 0.18, "sand": 0.05, "aggregate": 0.05, "bricks": 0.12}

# One bag of cement = 50 kg, so 20 bags per tonne
BAGS_PER_TONNE = 20