from datetime import datetime, date
from functools import wraps
from flask import Flask, jsonify, request, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from config import Config
from models import db, User, Material, MaterialRequest, Transaction, ImpactRecord, Notification

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Login required"}), 401
        return fn(*args, **kwargs)
    return wrapper

def notify(user_id, message):
    db.session.add(Notification(user_id=user_id, message=message))

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok", database="connected")
    except Exception:
        db.session.rollback()
        return jsonify(status="error", database="disconnected"), 500

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    role = str(data.get("role", "user")).lower()
    if not name or not email or not password:
        return jsonify(error="Name, email and password are required"), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400
    if role not in ("user", "provider", "seeker"):
        return jsonify(error="Role must be user, provider or seeker"), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="Email already registered"), 409
    user = User(name=name, email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify(message="Registration successful", user_id=user.user_id), 201

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(error="Invalid email or password"), 401
    session.clear()
    session["user_id"] = user.user_id
    return jsonify(message="Login successful", user=user.to_dict())

@app.post("/api/logout")
@login_required
def logout():
    session.clear()
    return jsonify(message="Logged out")

@app.get("/api/me")
@login_required
def me():
    user = db.session.get(User, session["user_id"])
    return jsonify(user.to_dict())

@app.get("/api/materials")
def list_materials():
    query = Material.query.filter_by(availability_status="available")
    category = request.args.get("category")
    search = request.args.get("search", "").strip()
    if category:
        query = query.filter(Material.category.ilike(f"%{category}%"))
    if search:
        query = query.filter(or_(Material.title.ilike(f"%{search}%"),
                                 Material.description.ilike(f"%{search}%"),
                                 Material.location.ilike(f"%{search}%")))
    return jsonify([m.to_dict() for m in query.order_by(Material.created_at.desc()).all()])

@app.post("/api/materials")
@login_required
def add_material():
    data = request.get_json(silent=True) or {}
    required = ("title", "category", "quantity", "unit", "condition", "location")
    missing = [key for key in required if data.get(key) in (None, "")]
    if missing:
        return jsonify(error="Missing fields: " + ", ".join(missing)), 400
    try:
        quantity = float(data["quantity"])
        price = float(data.get("price", 0) or 0)
    except (TypeError, ValueError):
        return jsonify(error="Quantity and price must be numeric"), 400
    if quantity <= 0 or price < 0:
        return jsonify(error="Quantity must be positive and price cannot be negative"), 400
    material = Material(
        user_id=session["user_id"], title=str(data["title"]).strip(),
        category=str(data["category"]).strip(), description=data.get("description", ""),
        quantity=quantity, unit=str(data["unit"]).strip(),
        condition=str(data["condition"]).strip(), location=str(data["location"]).strip(),
        price=price, is_free=bool(data.get("is_free", False))
    )
    db.session.add(material)
    db.session.commit()
    return jsonify(message="Material listed", material=material.to_dict()), 201

@app.put("/api/materials/<int:material_id>")
@login_required
def update_material(material_id):
    material = db.session.get(Material, material_id)
    if not material:
        return jsonify(error="Material not found"), 404
    if material.user_id != session["user_id"]:
        return jsonify(error="Not authorized"), 403
    data = request.get_json(silent=True) or {}
    for field in ("title", "category", "description", "unit", "condition", "location", "availability_status"):
        if field in data:
            setattr(material, field, data[field])
    for field in ("quantity", "price"):
        if field in data:
            try:
                value = float(data[field])
            except (TypeError, ValueError):
                return jsonify(error=f"{field} must be numeric"), 400
            if value < 0 or (field == "quantity" and value == 0):
                return jsonify(error=f"Invalid {field}"), 400
            setattr(material, field, value)
    if "is_free" in data:
        material.is_free = bool(data["is_free"])
    db.session.commit()
    return jsonify(message="Material updated", material=material.to_dict())

@app.delete("/api/materials/<int:material_id>")
@login_required
def archive_material(material_id):
    material = db.session.get(Material, material_id)
    if not material:
        return jsonify(error="Material not found"), 404
    if material.user_id != session["user_id"]:
        return jsonify(error="Not authorized"), 403
    material.availability_status = "archived"
    db.session.commit()
    return jsonify(message="Material archived")

@app.post("/api/requests")
@login_required
def create_request():
    data = request.get_json(silent=True) or {}
    try:
        material_id = int(data.get("material_id"))
        quantity = float(data.get("requested_quantity"))
    except (TypeError, ValueError):
        return jsonify(error="Valid material_id and requested_quantity are required"), 400
    material = db.session.get(Material, material_id)
    if not material or material.availability_status != "available":
        return jsonify(error="Material is unavailable"), 404
    if material.user_id == session["user_id"]:
        return jsonify(error="You cannot request your own material"), 400
    if quantity <= 0 or quantity > material.quantity:
        return jsonify(error="Requested quantity is not available"), 400
    item = MaterialRequest(material_id=material_id, seeker_id=session["user_id"],
                           message=data.get("message", ""), requested_quantity=quantity)
    db.session.add(item)
    notify(material.user_id, f"New request received for {material.title}.")
    db.session.commit()
    return jsonify(message="Request submitted", request=item.to_dict()), 201

@app.get("/api/requests")
@login_required
def my_requests():
    rows = MaterialRequest.query.filter_by(seeker_id=session["user_id"]).order_by(
        MaterialRequest.created_at.desc()).all()
    return jsonify([r.to_dict() for r in rows])

@app.get("/api/requests/received")
@login_required
def received_requests():
    material_ids = [m.material_id for m in Material.query.filter_by(user_id=session["user_id"]).all()]
    rows = MaterialRequest.query.filter(MaterialRequest.material_id.in_(material_ids)).all() if material_ids else []
    return jsonify([r.to_dict() for r in rows])

@app.put("/api/requests/<int:request_id>/status")
@login_required
def update_request(request_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ("accepted", "rejected"):
        return jsonify(error="Status must be accepted or rejected"), 400
    item = db.session.get(MaterialRequest, request_id)
    if not item:
        return jsonify(error="Request not found"), 404
    material = db.session.get(Material, item.material_id)
    if material.user_id != session["user_id"]:
        return jsonify(error="Not authorized"), 403
    if item.status != "pending":
        return jsonify(error="Request already processed"), 409
    if status == "accepted":
        if item.requested_quantity > material.quantity:
            return jsonify(error="Insufficient available quantity"), 400
        material.quantity -= item.requested_quantity
        if material.quantity == 0:
            material.availability_status = "unavailable"
        transaction = Transaction(request_id=item.request_id, status="pending")
        db.session.add(transaction)
    item.status = status
    notify(item.seeker_id, f"Your request for {material.title} was {status}.")
    db.session.commit()
    return jsonify(message=f"Request {status}")

@app.get("/api/transactions")
@login_required
def transactions():
    uid = session["user_id"]
    owned_ids = [m.material_id for m in Material.query.filter_by(user_id=uid).all()]
    rows = Transaction.query.join(MaterialRequest).filter(
        or_(MaterialRequest.seeker_id == uid,
            MaterialRequest.material_id.in_(owned_ids) if owned_ids else False)
    ).all()
    return jsonify([t.to_dict() for t in rows])

@app.put("/api/transactions/<int:transaction_id>/complete")
@login_required
def complete_transaction(transaction_id):
    tx = db.session.get(Transaction, transaction_id)
    if not tx:
        return jsonify(error="Transaction not found"), 404
    req = db.session.get(MaterialRequest, tx.request_id)
    material = db.session.get(Material, req.material_id)
    if session["user_id"] not in (req.seeker_id, material.user_id):
        return jsonify(error="Not authorized"), 403
    if tx.status == "completed":
        return jsonify(error="Already completed"), 409
    tx.status = "completed"
    tx.confirmed_at = datetime.utcnow()
    tx.collection_date = date.today()
    db.session.add(ImpactRecord(transaction_id=tx.transaction_id,
                                quantity_reused=req.requested_quantity, unit=material.unit,
                                calculation_note="Quantity reused through BuildBack"))
    notify(req.seeker_id, "Your material exchange was completed.")
    if material.user_id != req.seeker_id:
        notify(material.user_id, "Your material exchange was completed.")
    db.session.commit()
    return jsonify(message="Transaction completed")

@app.get("/api/impact")
@login_required
def impact():
    uid = session["user_id"]
    owned_ids = [m.material_id for m in Material.query.filter_by(user_id=uid).all()]
    rows = ImpactRecord.query.join(Transaction).join(MaterialRequest).join(Material).filter(
        or_(Material.user_id == uid, MaterialRequest.seeker_id == uid)
    ).all()
    return jsonify(total_records=len(rows),
                   total_quantity_reused=sum(float(r.quantity_reused) for r in rows),
                   records=[r.to_dict() for r in rows])

@app.get("/api/notifications")
@login_required
def notifications():
    rows = Notification.query.filter_by(user_id=session["user_id"]).order_by(
        Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in rows])

@app.put("/api/notifications/<int:notification_id>/read")
@login_required
def read_notification(notification_id):
    item = db.session.get(Notification, notification_id)
    if not item:
        return jsonify(error="Notification not found"), 404
    if item.user_id != session["user_id"]:
        return jsonify(error="Not authorized"), 403
    item.is_read = True
    db.session.commit()
    return jsonify(message="Notification marked read")

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify(error="API endpoint not found"), 404
    return "Page not found", 404

@app.errorhandler(500)
def server_error(_):
    db.session.rollback()
    return jsonify(error="Internal server error"), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("BuildBack database initialized.")
    app.run(debug=True)
