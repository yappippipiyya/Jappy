import os
from App.app_init_ import app

if __name__ == "__main__":
  # 開発環境のときのみHTTP許可
  os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

  app.run(debug=True, host="0.0.0.0")