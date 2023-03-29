from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'
db = SQLAlchemy(app)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Image {self.filename}>'

@app.route('/')
def index():
    images = Image.query.all()
    return render_template('index.html', images=images)

@app.route('/add', methods=['POST'])
def add_image():
    filename = request.form['filename']
    description = request.form['description']
    new_image = Image(filename=filename, description=description)
    db.session.add(new_image)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search_image():
    keyword = request.args.get('keyword')
    images = Image.query.filter(Image.description.contains(keyword)).all()
    return render_template('search_results.html', images=images)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
