from functools import wraps
from flask import abort, g, redirect, session, url_for
from .extensions import db
from .models import User


def current_user():
    if "user" not in g:
        g.user = db.session.get(User, session["uid"]) if "uid" in session else None
    return g.user


def require(*roles):
    """Role-based access control: @require() = any logged-in user, @require('supervisor') = that role only."""
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            u = current_user()
            if not u:
                return redirect(url_for("auth.login"))
            if roles and u.role not in roles:
                abort(403)
            return f(*a, **k)
        return w
    return deco


def members_only():
    u = current_user()
    if u.role != "supervisor" and not u.verified:
        abort(403, "Your account is awaiting verification by the supervisor.")


def register_filters(app):
    app.jinja_env.filters["dt"] = lambda v: v.strftime("%d %b, %H:%M") if v else ""
    app.jinja_env.filters["tm"] = lambda v: v.strftime("%H:%M") if v else ""
