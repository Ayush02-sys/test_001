import os
from flask import Flask
from config import Config
from .extensions import db
from .utils import current_user, register_filters


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    for d in (os.path.dirname(config.VAULT_KEY), config.UPLOAD_DIR, config.VAULT_DIR):
        os.makedirs(d, exist_ok=True)
    db.init_app(app)
    register_filters(app)
    app.context_processor(lambda: {"me": current_user()})

    from .controllers import auth, main, care, emergency, analytics
    for m in (auth, main, care, emergency, analytics):
        app.register_blueprint(m.bp)

    with app.app_context():
        db.create_all()          # tables are generated from app/models.py
        from .seed import seed
        seed()
    return app
