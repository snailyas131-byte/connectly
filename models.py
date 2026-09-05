from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

DEFAULT_CATEGORIES = ['Family', 'Friends', 'Work', 'Clients', 'University', 'Other']


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    contacts = db.relationship('Contact', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def init_default_categories(self):
        """Initializes default categories for a new user if none exist."""
        for name in DEFAULT_CATEGORIES:
            existing = Category.query.filter_by(user_id=self.id, name=name).first()
            if not existing:
                cat = Category(user_id=self.id, name=name)
                db.session.add(cat)
        db.session.commit()

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationship to contacts
    contacts = db.relationship('Contact', backref='category_rel', lazy='dynamic')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='uq_user_category_name'),
    )

    def __repr__(self):
        return f'<Category {self.name}>'


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=True)
    phone = db.Column(db.String(30), nullable=True, index=True)
    alternate_phone = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    company = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def initials(self):
        f = self.first_name[0].upper() if self.first_name else ''
        l = self.last_name[0].upper() if self.last_name else ''
        return f"{f}{l}" or '?'

    @property
    def category_name(self):
        if self.category_rel:
            return self.category_rel.name
        return 'Uncategorized'

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name or '',
            'full_name': self.full_name,
            'phone': self.phone or '',
            'alternate_phone': self.alternate_phone or '',
            'email': self.email or '',
            'company': self.company or '',
            'job_title': self.job_title or '',
            'address': self.address or '',
            'city': self.city or '',
            'birthday': self.birthday.strftime('%Y-%m-%d') if self.birthday else '',
            'notes': self.notes or '',
            'profile_picture': self.profile_picture,
            'is_favorite': self.is_favorite,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'initials': self.initials,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f'<Contact {self.full_name}>'
