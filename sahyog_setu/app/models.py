"""Model layer (M of MVC): the database schema lives here as SQLAlchemy classes."""
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pw = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)          # parent | senior | supervisor
    phone = db.Column(db.String(20))
    emergency_name = db.Column(db.String(120))
    emergency_phone = db.Column(db.String(20))
    verified = db.Column(db.Boolean, default=False)
    children = db.relationship("Child", backref="parent", cascade="all, delete-orphan")
    docs = db.relationship("Doc", backref="owner", cascade="all, delete-orphan")

    def set_password(self, p): self.pw = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.pw, p)


class Child(db.Model):
    __tablename__ = "children"
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    medical = db.Column(db.Text, default="")
    pref_name = db.Column(db.String(120))
    pref_phone = db.Column(db.String(20))


class Doc(db.Model):
    __tablename__ = "docs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kind = db.Column(db.String(60))
    fname = db.Column(db.String(200))
    stored = db.Column(db.String(80))                         # encrypted file name inside the vault
    status = db.Column(db.String(20), default="pending")
    created = db.Column(db.DateTime, default=datetime.now)

    @property
    def name(self): return self.owner.name


class Venue(db.Model):
    __tablename__ = "venues"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.Integer)


class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(40))
    name = db.Column(db.String(120))
    phone = db.Column(db.String(20))


class CareSession(db.Model):
    __tablename__ = "care_sessions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    activity = db.Column(db.String(60))
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)
    senior_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    venue_rel = db.relationship("Venue")
    host = db.relationship("User")

    @property
    def venue(self): return self.venue_rel.name
    @property
    def senior(self): return self.host.name if self.host else None


class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("care_sessions.id"), nullable=False)
    kind = db.Column(db.String(10), nullable=False)           # child | senior
    person_id = db.Column(db.Integer, nullable=False)
    check_in = db.Column(db.DateTime)
    check_out = db.Column(db.DateTime)

    @property
    def name(self):
        m = db.session.get(Child if self.kind == "child" else User, self.person_id)
        return m.name if m else "?"


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("care_sessions.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    caption = db.Column(db.Text)
    media = db.Column(db.String(200))
    created = db.Column(db.DateTime, default=datetime.now)
    care_session = db.relationship("CareSession")
    author_user = db.relationship("User")

    @property
    def title(self): return self.care_session.title
    @property
    def author(self): return self.author_user.name


class Emergency(db.Model):
    __tablename__ = "emergencies"
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)           # child | senior
    subject_id = db.Column(db.Integer, nullable=False)
    raised_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    note = db.Column(db.Text)
    created = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(10), default="open")
    resolved_at = db.Column(db.DateTime)

    @property
    def subject(self):
        m = db.session.get(Child if self.kind == "child" else User, self.subject_id)
        return m.name if m else "?"


class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    emergency_id = db.Column(db.Integer, db.ForeignKey("emergencies.id"))
    to_name = db.Column(db.String(120))
    to_phone = db.Column(db.String(20))
    channel = db.Column(db.String(10), default="SMS")
    created = db.Column(db.DateTime, default=datetime.now)
