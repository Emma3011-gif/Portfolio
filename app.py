import os
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///portfolio.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "emicyber20@gmail.com")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME", "emicyber20@gmail.com")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads", "projects")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

mail = Mail(app)
db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    live_url = db.Column(db.String(300), nullable=True)
    source_url = db.Column(db.String(300), nullable=True)
    tags = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_tags_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("index.html", projects=projects)


@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({"error": "All fields are required"}), 400

    try:
        msg = Message(
            subject=f"Portfolio Contact: {name}",
            sender=("Portfolio Contact", os.getenv("MAIL_USERNAME", "emicyber20@gmail.com")),
            recipients=["emicyber20@gmail.com"],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            reply_to=email,
        )
        mail.send(msg)
        return jsonify({"message": "Message sent successfully!"}), 200
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({"error": "Failed to send message. Please try again."}), 500


@app.route("/download-resume")
def download_resume():
    return send_from_directory(
        os.path.join(app.static_folder, "assets"),
        "Junior Software Developer Resume.pdf",
        as_attachment=True
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "")

        if username == admin_user and password == admin_pass:
            session["admin_logged_in"] = True
            session.permanent = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin/dashboard.html", projects=projects)


@app.route("/admin/projects/new", methods=["GET", "POST"])
@admin_required
def add_project():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        live_url = request.form.get("live_url", "").strip()
        source_url = request.form.get("source_url", "").strip()
        tags = request.form.get("tags", "").strip()

        if not title or not description:
            flash("Title and description are required", "error")
            return render_template("admin/add_project.html")

        image_url = None
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_url = f"uploads/projects/{filename}"

        project = Project(
            title=title,
            description=description,
            image_url=image_url,
            live_url=live_url or None,
            source_url=source_url or None,
            tags=tags or None,
        )
        db.session.add(project)
        db.session.commit()
        flash("Project added successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/add_project.html")


@app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == "POST":
        project.title = request.form.get("title", "").strip()
        project.description = request.form.get("description", "").strip()
        project.live_url = request.form.get("live_url", "").strip() or None
        project.source_url = request.form.get("source_url", "").strip() or None
        project.tags = request.form.get("tags", "").strip() or None

        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "" and allowed_file(file.filename):
                old_path = os.path.join(app.static_folder, project.image_url) if project.image_url else None
                if old_path and os.path.exists(old_path):
                    os.remove(old_path)
                filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                project.image_url = f"uploads/projects/{filename}"

        if not project.title or not project.description:
            flash("Title and description are required", "error")
            return render_template("admin/edit_project.html", project=project)

        project.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Project updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/edit_project.html", project=project)


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.image_url:
        old_path = os.path.join(app.static_folder, project.image_url)
        if os.path.exists(old_path):
            os.remove(old_path)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
