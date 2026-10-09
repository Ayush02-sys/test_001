"""Encrypted document storage (Fernet) kept outside the public static folder."""
import os
from cryptography.fernet import Fernet
from flask import current_app


def _f():
    key = current_app.config["VAULT_KEY"]
    if not os.path.exists(key):
        open(key, "wb").write(Fernet.generate_key())      # back this file up!
    return Fernet(open(key, "rb").read())


def store(data: bytes) -> str:
    name = os.urandom(8).hex() + ".enc"
    open(os.path.join(current_app.config["VAULT_DIR"], name), "wb").write(_f().encrypt(data))
    return name


def read(name: str) -> bytes:
    return _f().decrypt(open(os.path.join(current_app.config["VAULT_DIR"], name), "rb").read())
