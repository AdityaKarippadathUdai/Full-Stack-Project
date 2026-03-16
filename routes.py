from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import app, db, bcrypt, login_manager
from models import User, Book, BorrowedBook
from forms import RegisterForm, LoginForm, AddBookForm, BorrowBookForm
from datetime import datetime, timedelta, timezone

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@app.route("/home")
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        # Make the first user an admin for convenience
        is_first_user = User.query.count() == 0
        role = 'admin' if is_first_user else 'user'
        user = User(name=form.name.data, email=form.email.data, password=hashed_password, phone=form.phone.data, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if current_user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/dashboard")
@app.route("/mybooks")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    
    issued_books = BorrowedBook.query.filter_by(user_id=current_user.id).all()
    
    user_stats = {
        "name": current_user.name,
        "books_issued": len([b for b in issued_books if b.status == 'borrowed']),
        "books_returned": len([b for b in issued_books if b.status == 'returned']),
        "overdue": 0 # feature removed in db simplification
    }
    
    books = Book.query.all()
    return render_template("dashboard.html", user=user_stats, issued_books=issued_books, books=books)

@app.route("/books")
def books():
    all_books = Book.query.all()
    return render_template("books.html", books=all_books)

@app.route("/borrow/<int:book_id>")
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.quantity > 0:
        # Check if already borrowed currently
        existing_borrow = BorrowedBook.query.filter_by(user_id=current_user.id, book_id=book.id, status='borrowed').first()
        if existing_borrow:
            flash('You have already borrowed this book and not returned it yet.', 'warning')
            return redirect(url_for('books'))
            
        due_date = datetime.now(timezone.utc) + timedelta(days=30)
        borrow_record = BorrowedBook(user_id=current_user.id, book_id=book.id, return_date=due_date)
        
        book.quantity -= 1
            
        db.session.add(borrow_record)
        db.session.commit()
        
        return render_template("success.html", 
                               title="Book Borrowed Successfully!",
                               message=f"You have successfully borrowed '{book.title}'. Please return it by {due_date.strftime('%B %d, %Y')}.")
    else:
        flash('This book is currently unavailable.', 'danger')
        return redirect(url_for('books'))

@app.route("/return/<int:borrow_id>")
@login_required
def return_book(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)
    if borrow_record.user_id != current_user.id and current_user.role != 'admin':
        abort(403)
        
    if borrow_record.status == 'borrowed':
        borrow_record.status = 'returned'
        book = Book.query.get(borrow_record.book_id)
        book.quantity += 1
        db.session.commit()
        flash(f"Book '{book.title}' returned successfully.", 'success')
        
    return redirect(request.referrer or url_for('dashboard'))

# Admin Routes
@app.route("/admin")
@app.route("/admin/borrowed_books")
@login_required
@admin_required
def admin_dashboard():
    books = Book.query.all()
    borrowed_books_list = BorrowedBook.query.all()
    
    total_books = sum(b.quantity for b in books)
    available_qty = sum(b.quantity for b in books)
    total_issued = BorrowedBook.query.filter(BorrowedBook.status == 'borrowed').count()
    total_users = User.query.filter_by(role='user').count()
    
    # Format borrowed books for template
    borrowed_books = []
    for record in borrowed_books_list:
        book = Book.query.get(record.book_id)
        user = User.query.get(record.user_id)
        if book and user:
            borrowed_books.append({
                "id": record.id,
                "user_name": user.name,
                "book_title": book.title,
                "issue_date": record.borrow_date.strftime('%Y-%m-%d'),
                "due_date": record.return_date.strftime('%Y-%m-%d') if record.return_date else '',
                "status": record.status
            })
    
    # We will need the AddBookForm to pass to template or we can just redirect to a separate add-book page.
    form = AddBookForm()
    
    return render_template("admin_dashboard.html",
                           books=books,
                           borrowed_books=borrowed_books,
                           total_books=total_books,
                           available_books=available_qty,
                           total_issued=total_issued,
                           total_users=total_users,
                           form=form)

@app.route("/admin/add_book", methods=['POST'])
@login_required
@admin_required
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        book = Book(title=form.title.data, 
                    author=form.author.data, 
                    isbn=form.isbn.data, 
                    category=form.category.data, 
                    quantity=form.quantity.data)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
                
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/remove_book/<int:book_id>", methods=['POST'])
@login_required
@admin_required
def remove_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Check if currently borrowed
    active_borrows = BorrowedBook.query.filter_by(book_id=book.id).filter(BorrowedBook.status == 'borrowed').count()
    if active_borrows > 0:
        flash(f'Cannot remove book "{book.title}" because it is currently borrowed by {active_borrows} user(s).', 'warning')
    else:
        # Delete borrow history for this book to avoid foreign key constraints errors
        BorrowedBook.query.filter_by(book_id=book.id).delete()
        db.session.delete(book)
        db.session.commit()
        flash('Book removed successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/send_reminder/<int:borrow_id>", methods=['POST', 'GET'])
@login_required
@admin_required
def send_reminder(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)
    user = User.query.get(borrow_record.user_id)
    book = Book.query.get(borrow_record.book_id)
    
    if user and book:
        # For this prototype we will just flash a message representing an email sent.
        flash(f"Reminder email sent to {user.email} for '{book.title}'.", 'info')
    
    return redirect(url_for('admin_dashboard'))
