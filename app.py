import os
import resend
from functools import wraps
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db_url = os.getenv("DATABASE_URL", "sqlite:///portfolio.db")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url

resend.api_key = os.getenv("RESEND_API_KEY", "")
db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    live_url = db.Column(db.String(500), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    tags = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_tags_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    except Exception:
        projects = []
    return render_template("index.html", projects=projects)


@app.route("/api/contact", methods=["POST"])
def contact():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        message = data.get("message", "").strip()

        if not name or not email or not message:
            return jsonify({"error": "All fields are required"}), 400

        api_key = os.getenv("RESEND_API_KEY", "")
        if not api_key:
            print("No RESEND_API_KEY set")
            return jsonify({"error": "Email service not configured"}), 500

        resend.api_key = api_key

        params = {
            "from": os.getenv("RESEND_FROM_EMAIL", "Portfolio <onboarding@resend.dev>"),
            "to": ["emicyber20@gmail.com"],
            "subject": f"Portfolio Contact: {name}",
            "reply_to": email,
            "html": f"""
                <h2>New Portfolio Contact</h2>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <h3>Message:</h3>
                <p>{message.replace(chr(10), '<br>')}</p>
            """
        }

        email_response = resend.Emails.send(params)
        print(f"Email sent: {email_response}")
        return jsonify({"message": "Message sent successfully!"}), 200
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({"error": "Failed to send message. Please try again."}), 500


@app.route("/download-resume")
def download_resume():
    try:
        return send_from_directory(
            os.path.join(app.static_folder, "assets"),
            "Junior Software Developer Resume.pdf",
            as_attachment=True
        )
    except Exception as e:
        print(f"Download resume error: {e}")
        return "Resume not found", 404


@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404


@app.errorhandler(500)
def server_error(e):
    return "Internal server error", 500


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    try:
        if session.get("admin_logged_in"):
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            try:
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "")
                admin_user = os.getenv("ADMIN_USERNAME", "admin")
                admin_pass = os.getenv("ADMIN_PASSWORD", "")

                if username == admin_user and password == admin_pass:
                    session["admin_logged_in"] = True
                    session.permanent = True
                    return redirect(url_for("admin_dashboard"))
            except Exception as e:
                print(f"Admin login error: {e}")
            flash("Invalid credentials", "error")
        return render_template("admin/login.html")
    except Exception as e:
        print(f"Admin login route error: {e}")
        flash("An error occurred. Please try again.", "error")
        return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    try:
        session.pop("admin_logged_in", None)
    except Exception:
        pass
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
    except Exception as e:
        print(f"Dashboard query error: {e}")
        projects = []
    return render_template("admin/dashboard.html", projects=projects)


@app.route("/admin/projects/new", methods=["GET", "POST"])
@admin_required
def add_project():
    try:
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            image_url = request.form.get("image_url", "").strip()
            live_url = request.form.get("live_url", "").strip()
            source_url = request.form.get("source_url", "").strip()
            tags = request.form.get("tags", "").strip()

            if not title or not description:
                flash("Title and description are required", "error")
                return render_template("admin/add_project.html")

            project = Project(
                title=title,
                description=description,
                image_url=image_url or None,
                live_url=live_url or None,
                source_url=source_url or None,
                tags=tags or None,
            )
            try:
                db.session.add(project)
                db.session.commit()
                flash("Project added successfully!", "success")
            except Exception as e:
                db.session.rollback()
                print(f"Add project DB error: {e}")
                flash("Failed to add project. Please try again.", "error")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin/add_project.html")
    except Exception as e:
        print(f"Add project route error: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_project(project_id):
    try:
        try:
            project = Project.query.get_or_404(project_id)
        except Exception as e:
            print(f"Edit project lookup error: {e}")
            flash("Project not found.", "error")
            return redirect(url_for("admin_dashboard"))

        if request.method == "POST":
            try:
                project.title = request.form.get("title", "").strip()
                project.description = request.form.get("description", "").strip()
                project.image_url = request.form.get("image_url", "").strip() or None
                project.live_url = request.form.get("live_url", "").strip() or None
                project.source_url = request.form.get("source_url", "").strip() or None
                project.tags = request.form.get("tags", "").strip() or None
            except Exception as e:
                print(f"Edit project form parse error: {e}")
                flash("Invalid form data.", "error")
                return redirect(url_for("admin_dashboard"))

            if not project.title or not project.description:
                flash("Title and description are required", "error")
                return render_template("admin/edit_project.html", project=project)

            project.updated_at = datetime.utcnow()
            try:
                db.session.commit()
                flash("Project updated successfully!", "success")
            except Exception as e:
                db.session.rollback()
                print(f"Edit project DB error: {e}")
                flash("Failed to update project. Please try again.", "error")
            return redirect(url_for("admin_dashboard"))

        return render_template("admin/edit_project.html", project=project)
    except Exception as e:
        print(f"Edit project route error: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for("admin_dashboard"))


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def delete_project(project_id):
    try:
        try:
            project = Project.query.get_or_404(project_id)
        except Exception as e:
            print(f"Delete project lookup error: {e}")
            flash("Project not found.", "error")
            return redirect(url_for("admin_dashboard"))
        try:
            db.session.delete(project)
            db.session.commit()
            flash("Project deleted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Delete project DB error: {e}")
            flash("Failed to delete project.", "error")
    except Exception as e:
        print(f"Delete project route error: {e}")
        flash("An error occurred. Please try again.", "error")
    return redirect(url_for("admin_dashboard"))


try:
    with app.app_context():
        db.create_all()
        if Project.query.count() == 0:
            defaults = [
                Project(
                    title="Ejikeugboaja Foundation",
                    description="A foundation website built to showcase the organization's mission, initiatives, and community impact with a clean, modern design.",
                    image_url="https://img.icons8.com/external-vitaliy-gorbachev-lineal-vitaly-gorbachev/120/external-foundation-charity-vitaliy-gorbachev-lineal-vitaly-gorbachev-2.png",
                    live_url="https://ejikeugboajafoundation.org",
                    source_url="https://github.com/Emma3011-gif/ejikeugboajafoundation",
                    tags="WordPress, PHP, HTML5, CSS3",
                ),
                Project(
                    title="Weather Dashboard",
                    description="Real-time weather application with location-based forecasts, interactive maps, and dynamic visualizations.",
                    image_url="https://img.icons8.com/external-vitaliy-gorbachev-lineal-vitaly-gorbachev/120/external-weather-weather-forecast-vitaliy-gorbachev-lineal-vitaly-gorbachev.png",
                    live_url="#",
                    source_url="#",
                    tags="React, API, CSS3, Chart.js",
                ),
                Project(
                    title="To-Do List App",
                    description="A clean and intuitive task management app with add, edit, delete, and mark-complete functionality built for everyday productivity.",
                    image_url="https://img.icons8.com/external-vitaliy-gorbachev-lineal-vitaly-gorbachev/120/external-to-do-list-checklist-vitaliy-gorbachev-lineal-vitaly-gorbachev.png",
                    live_url="https://to-do-list-ddjg.vercel.app",
                    source_url="https://github.com/Emma3011-gif",
                    tags="React, JavaScript, CSS3, Vercel",
                ),
            ]
            db.session.bulk_save_objects(defaults)
            db.session.commit()
            print("Seeded 3 default projects")
except Exception as e:
    print(f"DB init error: {e}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
