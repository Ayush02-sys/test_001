import os
from datetime import datetime
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Attendance, CareSession, Child, Post, User, Venue
from ..utils import current_user, members_only, require

bp = Blueprint("care", __name__)
FMT = "%Y-%m-%dT%H:%M"


def verified_seniors():
    return User.query.filter_by(role="senior", verified=True).all()


@bp.route("/sessions", methods=["GET", "POST"])
@require()
def sessions():
    if request.method == "POST":
        if current_user().role != "supervisor":
            abort(403)
        f = request.form
        s, e, v = datetime.strptime(f["start"], FMT), datetime.strptime(f["end"], FMT), int(f["venue_id"])
        if e <= s:
            flash("End time must be after start time.")
        elif CareSession.query.filter(CareSession.venue_id == v, CareSession.start < e, CareSession.end > s).first():
            flash("That venue is already booked for this slot.")
        else:
            db.session.add(CareSession(title=f["title"], activity=f["activity"], venue_id=v, start=s, end=e,
                                       senior_id=int(f["senior_id"]) if f["senior_id"] else None))
            db.session.commit()
            flash("Session scheduled.")
        return redirect(url_for("care.sessions"))
    return render_template("sessions.html", venues=Venue.query.all(), seniors=verified_seniors(),
                           rows=CareSession.query.order_by(CareSession.start.desc()).limit(40).all())


@bp.route("/sessions/<int:i>")
@require()
def session_view(i):
    members_only()
    return render_template("session.html", s=db.get_or_404(CareSession, i), seniors=verified_seniors(),
        att=Attendance.query.filter_by(session_id=i).all(),
        posts=Post.query.filter_by(session_id=i).order_by(Post.id.desc()).all(),
        kids=Child.query.join(Child.parent).filter(User.verified.is_(True)).all())


@bp.post("/attend")
@require("supervisor")
def attend():
    f = request.form
    sid, (kind, pid) = int(f["session_id"]), f["who"].split(":")
    rec = Attendance.query.filter_by(session_id=sid, kind=kind, person_id=int(pid)).first()
    if f["act"] == "in" and not rec:
        db.session.add(Attendance(session_id=sid, kind=kind, person_id=int(pid), check_in=datetime.now()))
    elif f["act"] == "out" and rec and not rec.check_out:
        rec.check_out = datetime.now()
    db.session.commit()
    return redirect(url_for("care.session_view", i=sid))


@bp.post("/post")
@require("supervisor")
def post():
    m, name = request.files.get("media"), None
    if m and m.filename:
        name = os.urandom(6).hex() + "_" + secure_filename(m.filename)
        m.save(os.path.join(current_app.config["UPLOAD_DIR"], name))
    sid = int(request.form["session_id"])
    db.session.add(Post(session_id=sid, author_id=current_user().id, caption=request.form["caption"], media=name))
    db.session.commit()
    return redirect(url_for("care.session_view", i=sid))


@bp.route("/feed")
@require()
def feed():
    members_only()
    return render_template("feed.html", posts=Post.query.order_by(Post.id.desc()).limit(30).all())
