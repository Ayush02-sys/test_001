from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import User

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        if f["role"] not in ("parent", "senior"):
            abort(400)
        u = User(name=f["name"], email=f["email"].lower(), role=f["role"], phone=f["phone"],
                 emergency_name=f["emergency_name"], emergency_phone=f["emergency_phone"])
        u.set_password(f["password"])
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That email is already registered.")
            return redirect(url_for("auth.register"))
        session["uid"] = u.id
        flash("Registered. Upload your documents so the supervisor can verify you.")
        return redirect(url_for("main.dash"))
    return render_template("auth.html", mode="register")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(email=request.form["email"].lower()).first()
        if u and u.check_password(request.form["password"]):
            session["uid"] = u.id
            return redirect(url_for("main.dash"))
        flash("Wrong email or password.")
    return render_template("auth.html", mode="login")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
