import io
from datetime import datetime
from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import CareSession, Child, Doc, Emergency, User
from ..services import vault
from ..utils import current_user, require

bp = Blueprint("main", __name__)


@bp.route("/")
@require()
def dash():
    u = current_user()
    return render_template("dash.html", kids=u.children, docs=sorted(u.docs, key=lambda d: -d.id),
        upcoming=CareSession.query.filter(CareSession.end >= datetime.now()).order_by(CareSession.start).limit(6).all(),
        pending=User.query.filter(User.role != "supervisor", User.verified.is_(False)).count(),
        open_em=Emergency.query.filter_by(status="open").count())


@bp.post("/children")
@require("parent")
def add_child():
    f = request.form
    db.session.add(Child(parent_id=current_user().id, name=f["name"], age=int(f["age"]), medical=f["medical"],
                         pref_name=f["pref_name"], pref_phone=f["pref_phone"]))
    db.session.commit()
    return redirect(url_for("main.dash"))


@bp.post("/docs")
@require("parent", "senior")
def upload_doc():
    f = request.files["file"]
    if not f.filename:
        abort(400)
    db.session.add(Doc(user_id=current_user().id, kind=request.form["kind"], fname=secure_filename(f.filename),
                       stored=vault.store(f.read())))
    db.session.commit()
    flash("Document encrypted and stored in your vault.")
    return redirect(url_for("main.dash"))


@bp.route("/docs/<int:i>")
@require()
def get_doc(i):
    d = db.get_or_404(Doc, i)
    if current_user().role != "supervisor" and d.user_id != current_user().id:
        abort(403)
    return send_file(io.BytesIO(vault.read(d.stored)), download_name=d.fname, as_attachment=True)
