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
import re

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


class FillerWord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(80), nullable=False)


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


@app.route("/search", methods=["GET", "POST"])
def search_image(keywords=None):
    if request.method == "GET":
        keywords = request.args.get("keywords")
        words = (
            re.sub(r"'s", "", keywords.replace(",", " ").replace(".", ""))
            .replace("[fn]", "")
            .split()
        )
    elif request.method == "POST":
        query = request.form["keyword"]
        words = re.sub(
            r"'s", "", query.replace(",", "").replace(".", "").replace("[fn]", "")
        ).split()
    else:
        return render_template("index.html")

    filler_words = [filler_word.word for filler_word in FillerWord.query.all()]
    words = [word for word in words if word not in filler_words]

    results = {}
    for word in words:
        associated_images = list()
        image_results = Image.query.filter(Image.description.contains(word)).all()
        for image_result in image_results:
            keywords = (
                image_result.description.replace(" ", "")
                .replace("-", ",")
                .replace('"', "")
                .split(",")
            )
            descriptions = [keyword.lower() for keyword in keywords]
            if word.lower() in descriptions:
                associated_images.append(image_result)
        results[word] = associated_images
    return render_template("search_results.html", images=results)


@app.route("/delete/<int:image_id>", methods=["POST"])
def delete_image(image_id):
    image = Image.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/uploads/images/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOADED_IMAGES_DEST"], filename)


@app.route("/add_filler_word", methods=["POST"])
def add_filler_word():
    word = request.form["word"]
    keywords = request.form["keywords"]
    new_filler_word = FillerWord(word=word)
    db.session.add(new_filler_word)
    db.session.commit()
    return redirect(url_for("search_image", keywords=keywords))


@app.route("/update-description/<int:image_id>", methods=["POST"])
def update_description(image_id):
    image = Image.query.get_or_404(image_id)
    new_description = request.form["description"]
    image.description = new_description
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/filler_words")
def filler_words():
    filler_words = FillerWord.query.all()
    return render_template("filler_words.html", filler_words=filler_words)


@app.route("/update_filler_word/<int:word_id>", methods=["POST"])
def update_filler_word(word_id):
    filler_word = FillerWord.query.get_or_404(word_id)
    new_word = request.form["word"]
    filler_word.word = new_word
    db.session.commit()
    return redirect(url_for("filler_words"))


@app.route("/delete_filler_word/<int:word_id>", methods=["POST"])
def delete_filler_word(word_id):
    filler_word = FillerWord.query.get_or_404(word_id)
    db.session.delete(filler_word)
    db.session.commit()
    return redirect(url_for("filler_words"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
