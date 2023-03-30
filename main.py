from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
    send_file,
)
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///images.db"
app.config["UPLOADED_IMAGES_DEST"] = "uploads/images"
app.config["UPLOADED_IMAGES_URL"] = "uploads/images/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
db = SQLAlchemy(app)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Image {self.filename}>"


@app.route("/")
def index():
    images = Image.query.all()
    return render_template("index.html", images=images)


@app.route("/add_image", methods=["POST"])
def add_image():
    if request.method == "POST":
        file = request.files["file"]
        description = request.form["description"]

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            new_image = Image(file_path=filename, description=description)
            db.session.add(new_image)
            db.session.commit()

            return redirect(url_for("index"))

    return render_template("index.html")


@app.route("/uploads/<path:filename>")
def serve_uploaded_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    return send_file(file_path, as_attachment=True)


@app.route("/search", methods=["GET"])
def search_image():
    keyword = request.args.get("keyword")
    images = Image.query.filter(Image.description.contains(keyword)).all()
    return render_template("search_results.html", images=images)


@app.route("/delete/<int:image_id>", methods=["POST"])
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/uploads/images/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOADED_IMAGES_DEST"], filename)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
