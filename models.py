from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_id(self):
        return str(self.user_id)

    def to_dict(self):
        return {"user_id": self.user_id, "name": self.name, "email": self.email, "role": self.role}

class Material(db.Model):
    __tablename__ = "materials"
    material_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), default=0)
    is_free = db.Column(db.Boolean, default=False)
    image_path = db.Column(db.String(255))
    availability_status = db.Column(db.String(30), default="available")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"material_id": self.material_id, "user_id": self.user_id, "title": self.title,
                "category": self.category, "description": self.description, "quantity": self.quantity,
                "unit": self.unit, "condition": self.condition, "location": self.location,
                "price": float(self.price or 0), "is_free": self.is_free,
                "availability_status": self.availability_status,
                "created_at": self.created_at.isoformat() if self.created_at else None}

class MaterialRequest(db.Model):
    __tablename__ = "requests"
    request_id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.material_id"), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    message = db.Column(db.Text)
    requested_quantity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"request_id": self.request_id, "material_id": self.material_id,
                "seeker_id": self.seeker_id, "message": self.message,
                "requested_quantity": self.requested_quantity, "status": self.status,
                "created_at": self.created_at.isoformat() if self.created_at else None}

class Transaction(db.Model):
    __tablename__ = "transactions"
    transaction_id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("requests.request_id"), unique=True, nullable=False)
    status = db.Column(db.String(30), default="pending")
    collection_date = db.Column(db.Date)
    confirmed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {"transaction_id": self.transaction_id, "request_id": self.request_id,
                "status": self.status,
                "collection_date": self.collection_date.isoformat() if self.collection_date else None}

class ImpactRecord(db.Model):
    __tablename__ = "impact_records"
    record_id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.transaction_id"), unique=True, nullable=False)
    quantity_reused = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    calculation_note = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"record_id": self.record_id, "transaction_id": self.transaction_id,
                "quantity_reused": self.quantity_reused, "unit": self.unit,
                "calculation_note": self.calculation_note,
                "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None}

class Notification(db.Model):
    __tablename__ = "notifications"
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"notification_id": self.notification_id, "message": self.message,
                "is_read": self.is_read,
                "created_at": self.created_at.isoformat() if self.created_at else None}
