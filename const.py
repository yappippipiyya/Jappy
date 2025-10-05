import os
from dotenv import load_dotenv



FONT_NAME = "Noto Sans JP"
FONT_NAME_BOLD = "Noto Sans JP Bold"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_DIR = os.path.join(BASE_DIR, ".env")

load_dotenv(DOTENV_DIR, override=True)

REDIRECT_URI = os.environ.get("REDIRECT_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")

HOST = os.getenv("host", "")
USER = os.getenv("user", "")
PASSWORD = os.getenv("password", "")
DB_NAME = os.getenv("db_name", "")


LINE_AUTHORIZATION_URL = 'https://access.line.me/dialog/oauth/weblogin'
LINE_TOKEN_URL = 'https://api.line.me/v2/oauth/accessToken'
LINE_USER_INFO_URL = 'https://api.line.me/v2/profile'

CLIENT_ID = os.environ.get("cliend_id")
CLIENT_SECRET = os.environ.get("client_secret")