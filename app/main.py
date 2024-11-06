from flask import Flask, render_template, request, redirect, url_for
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize app
app = Flask(__name__)
api = Api(app)

# Configure the SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'books.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Book {self.title}>"

# Create an application context
with app.app_context():
    # Create the database and tables
    db.create_all()

# RESTful API
book_parser = reqparse.RequestParser()
book_parser.add_argument('title', type=str, required=True, help='Title cannot be blank!')
book_parser.add_argument('author', type=str, required=True, help='Author cannot be blank!')

class BookResource(Resource):
    def get(self, book_id):
        book = Book.query.get(book_id)
        if not book:
            return {'message': 'Book not found'}, 404
        return {'id': book.id, 'title': book.title, 'author': book.author}

    def delete(self, book_id):
        book = Book.query.get(book_id)
        if not book:
            return {'message': 'Book not found'}, 404
        db.session.delete(book)
        db.session.commit()
        return {'message': 'Book deleted'}

class BookListResource(Resource):
    def get(self):
        books = Book.query.all()
        return [{'id': book.id, 'title': book.title, 'author': book.author} for book in books]

    def post(self):
        args = book_parser.parse_args()
        new_book = Book(title=args['title'], author=args['author'])
        db.session.add(new_book)
        db.session.commit()
        return {'id': new_book.id, 'title': new_book.title, 'author': new_book.author}, 201

# Add API routes
api.add_resource(BookListResource, '/api/books')
api.add_resource(BookResource, '/api/books/<int:book_id>')

# Web frontend
@app.route('/')
def index():
    with app.app_context():
        books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/add', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    new_book = Book(title=title, author=author)
    db.session.add(new_book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:book_id>', methods=['GET'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        db.session.delete(book)
        db.session.commit()
    return redirect(url_for('index'))

# Run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
