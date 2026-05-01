import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "emicyber20@gmail.com")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME", "emicyber20@gmail.com")

mail = Mail(app)


@app.route("/")
def index():
    return render_template("index.html")


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
