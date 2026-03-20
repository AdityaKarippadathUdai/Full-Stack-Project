from datetime import datetime, timezone
from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(10), default='user') # 'user' or 'admin'
    
    # Relationship with BorrowedBooks
    borrowed_books = db.relationship('BorrowedBook', backref='borrower', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    
    # Relationship with BorrowedBooks
    borrow_records = db.relationship('BorrowedBook', backref='book', lazy=True)

    def __repr__(self):
        return f"Book('{self.title}', '{self.author}', '{self.category}', Quantity: {self.quantity})"

class BorrowedBook(db.Model):
    __tablename__ = 'borrowed_books'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    requested_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    borrow_date = db.Column(db.DateTime, nullable=True)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending') # 'pending', 'approved', 'rejected', 'returned'
    last_reminder_at = db.Column(db.DateTime, nullable=True)
    reminder_count   = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"BorrowedBook(User ID: {self.user_id}, Book ID: {self.book_id}, Status: {self.status})"

class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f"Notification(User: {self.user_id}, Read: {self.is_read})"
