import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    # MySQL from XAMPP (default XAMPP login: root, no password)
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "kaingo_db")

    # SMTP (Gmail: use an App Password). If empty, emails are printed in the terminal instead.
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")

    BRAND = "KainGo"
    RESTAURANT_NAME = "Panyero's Place"   # change this to your client
    MAX_CALL_ATTEMPTS = 3                  # unanswered calls before the order is cancelled

    # profile photo uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
    MENU_IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "static", "img", "menu")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024        # 2 MB

    WTF_CSRF_TIME_LIMIT = None                  # a CSRF token stays valid for the whole login session
