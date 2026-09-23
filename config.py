from pathlib import Path

# ==============================
# Telegram
# ==============================

BOT_TOKEN = "8736230733:AAHxOAMWWBYijRrgbAhhosz3cXbjYt25TfI"

# Telegram ID адміністратора
ADMIN_ID = 6229500744

# ID каналу, куди бот буде відправляти розклад.
# Для каналу зазвичай це число виду -1001234567890
CHANNEL_ID = -1001234567890

# Посилання на портфоліо
PORTFOLIO_URL = "https://example.com"

# ==============================
# Часова зона
# ==============================

TIMEZONE = "Europe/Kyiv"

# ==============================
# База даних
# ==============================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "bot.db"