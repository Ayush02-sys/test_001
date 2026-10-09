"""Demo data so the dashboards and analytics are populated on first run."""
import random
from datetime import datetime, timedelta
from .extensions import db
from .models import (Attendance, CareSession, Child, Contact, Emergency, Post, User, Venue)


def seed():
    if User.query.first():
        return
    rnd = random.Random(7)

    def user(name, email, role, phone, en="", ep=""):
        u = User(name=name, email=email, role=role, phone=phone, emergency_name=en, emergency_phone=ep, verified=True)
        u.set_password("demo123")
        db.session.add(u)
        return u

    sup = user("Ravi Sharma (Supervisor)", "supervisor@demo.in", "supervisor", "9000000001")
    seniors = [user(n, e, "senior", f"90000001{i}", f"{n.split()[1]} family", f"98000001{i}") for i, (n, e) in enumerate(
        [("Kamla Devi", "senior@demo.in"), ("Mohan Lal", "s2@demo.in"), ("Sudha Rao", "s3@demo.in"), ("Iqbal Khan", "s4@demo.in")])]
    kids = []
    for i, (p, k) in enumerate([("Anita Verma", "Aarav"), ("Rohit Mehta", "Diya"), ("Neha Gupta", "Kabir"),
                                ("Sanjay Iyer", "Meera"), ("Pooja Singh", "Vihaan"), ("Arjun Nair", "Isha")]):
        parent = user(p, "parent@demo.in" if i == 0 else f"p{i}@demo.in", "parent", f"91000000{i}")
        c = Child(parent=parent, name=k, age=rnd.randint(4, 11), medical="", pref_name="Grandparent", pref_phone=f"97000000{i}")
        db.session.add(c)
        kids.append(c)
    vens = [Venue(name=n, capacity=c) for n, c in (("Community Hall", 30), ("Central Garden", 40), ("Library Room", 12))]
    db.session.add_all(vens + [Contact(kind=k, name=n, phone=p) for k, n, p in (
        ("Hospital", "City Care Hospital", "0522-100200"), ("Police", "Colony Beat Police", "100"), ("Ambulance", "Ambulance", "108"))])
    db.session.flush()

    acts = ["Storytelling", "Gardening", "Arts & crafts", "Traditional games", "Mentoring"]
    mon = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now().weekday() + 56)
    for w in range(10):
        for d in (0, 2, 5):
            st = mon + timedelta(weeks=w, days=d)
            a = rnd.choice(acts)
            s = CareSession(title=f"{a} circle", activity=a, venue_id=rnd.choice(vens).id, senior_id=rnd.choice(seniors).id,
                            start=st, end=st + timedelta(hours=2))
            db.session.add(s)
            db.session.flush()
            if st > datetime.now():
                continue
            for c in rnd.sample(kids, rnd.randint(3, 6)):
                db.session.add(Attendance(session_id=s.id, kind="child", person_id=c.id, check_in=st,
                                          check_out=st + timedelta(minutes=rnd.randint(60, 120))))
            for o in rnd.sample(seniors, rnd.randint(1, 2)):
                db.session.add(Attendance(session_id=s.id, kind="senior", person_id=o.id, check_in=st, check_out=st + timedelta(hours=2)))
            db.session.add(Post(session_id=s.id, author_id=sup.id, caption=f"Today's {a.lower()} session went wonderfully!",
                                created=st + timedelta(hours=1)))
    for i in range(4):
        t = datetime.now() - timedelta(days=rnd.randint(2, 40))
        db.session.add(Emergency(kind="child", subject_id=kids[i].id, raised_by=sup.id, note="Minor fall", created=t,
                                 status="resolved", resolved_at=t + timedelta(minutes=rnd.randint(4, 15))))
    db.session.commit()
