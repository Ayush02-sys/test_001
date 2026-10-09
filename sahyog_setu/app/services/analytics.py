from datetime import datetime
import pandas as pd
from ..extensions import db
from ..models import Attendance, CareSession, Emergency, Venue


def analytics():
    S = db.session
    att = pd.read_sql(S.query(Attendance.kind, Attendance.person_id, Attendance.session_id, Attendance.check_in,
        Attendance.check_out, CareSession.activity, CareSession.start, Venue.capacity, Venue.name.label("venue"))
        .join(CareSession, CareSession.id == Attendance.session_id)
        .join(Venue, Venue.id == CareSession.venue_id).statement, db.engine)
    ses = pd.read_sql(S.query(CareSession.start, CareSession.end, Venue.name.label("venue"))
        .join(Venue, Venue.id == CareSession.venue_id).filter(CareSession.start <= datetime.now()).statement, db.engine)
    em = pd.read_sql(S.query(Emergency.created, Emergency.resolved_at).statement, db.engine)
    D = lambda s: {str(k): round(float(v), 1) for k, v in s.items()}
    r = {"kpi": dict(child_hours=0, senior_hours=0, kids=0, seniors=0, sessions=len(ses), emergencies=len(em), response=0),
         "weekly": {"labels": [], "child": [], "senior": []}, "activity": {}, "occupancy": {}, "venue": {}}
    if not att.empty:
        att["hrs"] = ((pd.to_datetime(att.check_out) - pd.to_datetime(att.check_in)).dt.total_seconds() / 3600).fillna(0)
        att["wk"] = pd.to_datetime(att.start).dt.to_period("W").dt.start_time
        w = att.pivot_table(index="wk", columns="kind", values="hrs", aggfunc="sum", fill_value=0)
        w = w.reindex(columns=["child", "senior"], fill_value=0)
        r["weekly"] = {"labels": [i.strftime("%d %b") for i in w.index],
                       "child": w.child.round(1).tolist(), "senior": w.senior.round(1).tolist()}
        kids, old = att[att.kind == "child"], att[att.kind == "senior"]
        r["activity"] = D(kids.groupby("activity").size().sort_values(ascending=False))
        per = kids.groupby(["venue", "session_id"]).agg(n=("person_id", "size"), cap=("capacity", "first")).reset_index()
        r["occupancy"] = D((per.n / per.cap * 100).groupby(per.venue).mean())
        r["kpi"].update(child_hours=round(float(kids.hrs.sum()), 1), kids=int(kids.person_id.nunique()),
                        senior_hours=round(float(old.hrs.sum()), 1), seniors=int(old.person_id.nunique()))
    if not ses.empty:
        ses["h"] = (pd.to_datetime(ses.end) - pd.to_datetime(ses.start)).dt.total_seconds() / 3600
        r["venue"] = D(ses.groupby("venue").h.sum())
    done = em.dropna(subset=["resolved_at"])
    if not done.empty:
        r["kpi"]["response"] = round(float((pd.to_datetime(done.resolved_at) - pd.to_datetime(done.created))
                                           .dt.total_seconds().mean() / 60), 1)
    return r
