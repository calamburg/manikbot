from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
ID = os.getenv("ID")



PORTFOLIO_URL = "https://example.com"


TIMEZONE = "Europe/Kyiv"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "bot.db"