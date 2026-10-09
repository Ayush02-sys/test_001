from datetime import datetime
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from ..extensions import db
from ..models import Alert, Child, Contact, Doc, Emergency, User
from ..services.notifier import notify
from ..utils import current_user, require

bp = Blueprint("emergency", __name__)


@bp.post("/sos")
@require()
def sos():
    u, note = current_user(), request.form.get("note", "")
    kind, pid = request.form["who"].split(":")
    if kind == "child":
        c = db.get_or_404(Child, int(pid))
        if u.role == "senior" or (u.role == "parent" and c.parent_id != u.id):
            abort(403)
        subject, targets = c.name, [(c.parent.name, c.parent.phone), (c.pref_name, c.pref_phone)]
    else:
        s = db.get_or_404(User, int(pid))
        if s.role != "senior" or (u.role != "supervisor" and u.id != s.id):
            abort(403)
        subject, targets = s.name, [(s.emergency_name, s.emergency_phone)]
    em = Emergency(kind=kind, subject_id=int(pid), raised_by=u.id, note=note)
    db.session.add(em)
    db.session.flush()
    targets += [(v.name, v.phone) for v in User.query.filter_by(role="supervisor")]
    sent = list(dict.fromkeys(targets))
    for n, ph in sent:
        notify(em, n, ph, f"EMERGENCY: {subject} ({kind}) needs help. {note}".strip())
    db.session.commit()
    flash(f"Emergency alert sent to {len(sent)} contacts.")
    return redirect(request.referrer or url_for("main.dash"))


@bp.route("/admin")
@require("supervisor")
def admin():
    return render_template("admin.html", users=User.query.filter(User.role != "supervisor").order_by(User.verified, User.id).all(),
        docs=Doc.query.order_by((Doc.status == "pending").desc(), Doc.id.desc()).all(),
        ems=Emergency.query.order_by(Emergency.status, Emergency.id.desc()).limit(15).all(),
        alerts=Alert.query.order_by(Alert.id.desc()).limit(8).all(), contacts=Contact.query.all(),
        kids=Child.query.all(), seniors=User.query.filter_by(role="senior").all())


@bp.post("/act")
@require("supervisor")
def act():
    f = request.form
    i = int(f["id"])
    if f["what"] == "user":
        db.get_or_404(User, i).verified = f["ok"] == "1"
    elif f["what"] == "doc":
        db.get_or_404(Doc, i).status = "approved" if f["ok"] == "1" else "rejected"
    else:
        e = db.get_or_404(Emergency, i)
        e.status, e.resolved_at = "resolved", datetime.now()
    db.session.commit()
    return redirect(url_for("emergency.admin"))
