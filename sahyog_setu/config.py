import os
BASE = os.path.abspath(os.path.dirname(__file__))
INSTANCE = os.path.join(BASE, "instance")      # private data: never served over HTTP

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE, "sahyog.db")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_DIR = os.path.join(BASE, "app", "static", "uploads")   # public photos / videos
    VAULT_DIR = os.path.join(INSTANCE, "vault")                   # encrypted documents
    VAULT_KEY = os.path.join(INSTANCE, "vault.key")
