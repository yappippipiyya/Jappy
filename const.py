import os
from dotenv import load_dotenv



FONT_NAME = "Noto Sans JP"
FONT_NAME_BOLD = "Noto Sans JP Bold"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_DIR = os.path.join(BASE_DIR, ".env")

load_dotenv(DOTENV_DIR, override=True)

# Google OAuth 2.0の設定
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")

DATABASE_URL = os.getenv("DATABASE_URL", "")

HOST = os.getenv("host", "")
USER = os.getenv("user", "")
PASSWORD = os.getenv("password", "")
DB_NAME = os.getenv("db_name", "")