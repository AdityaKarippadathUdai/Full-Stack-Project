from flask import render_template, url_for, flash, redirect, request, abort, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from extensions import db, bcrypt, login_manager
from models import User, Book, BorrowedBook
from forms import RegisterForm, LoginForm, AddBookForm, BorrowBookForm
from datetime import datetime, timedelta, timezone

main = Blueprint('main', __name__)

@main.app_context_processor
def inject_now():
    return {'current_year': datetime.now().year}

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

@main.route("/")
@main.route("/home")
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
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
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login failed. Check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route("/dashboard")
@main.route("/mybooks")
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    
    borrowed_books = BorrowedBook.query.filter_by(user_id=current_user.id).all()
    
    user_stats = {
        "name": current_user.name,
        "books_borrowed": len([b for b in borrowed_books if b.status == 'approved']),
        "books_returned": len([b for b in borrowed_books if b.status == 'returned']),
        "overdue": 0 # feature removed in db simplification
    }
    
    books = Book.query.all()
    return render_template("dashboard.html", user=user_stats, borrowed_books=borrowed_books, books=books)

@main.route("/books")
def books():
    all_books = Book.query.all()
    return render_template("books.html", books=all_books)

@main.route("/borrow/<int:book_id>", methods=['POST'])
@login_required
def borrow_book(book_id):
    if current_user.role == 'admin':
        flash('Administrators cannot request or borrow books.', 'danger')
        return redirect(url_for('main.admin_dashboard'))
    
    book = Book.query.get_or_404(book_id)
    if book.quantity > 0:
        # Check if already has a pending or approved borrow for this book
        existing_request = BorrowedBook.query.filter_by(user_id=current_user.id, book_id=book.id).filter(BorrowedBook.status.in_(['pending', 'approved'])).first()
        if existing_request:
            if existing_request.status == 'pending':
                flash('You have already requested to borrow this book. Please wait for admin approval.', 'info')
            else:
                flash('You have already borrowed this book and not returned it yet.', 'warning')
            return redirect(url_for('main.books'))
            
        borrow_request = BorrowedBook(user_id=current_user.id, book_id=book.id, status='pending', requested_at=datetime.now(timezone.utc))
            
        db.session.add(borrow_request)
        db.session.commit()
        
        flash(f"Your request to borrow '{book.title}' has been submitted and is pending admin approval.", 'success')
        return redirect(url_for('main.dashboard'))
    else:
        flash('This book is currently unavailable.', 'danger')
        return redirect(url_for('main.books'))

@main.route("/return/<int:borrow_id>")
@login_required
@admin_required
def return_book(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)
    
    if borrow_record.status == 'approved':
        borrow_record.status = 'returned'
        book = Book.query.get(borrow_record.book_id)
        book.quantity += 1
        db.session.commit()
        flash(f"Book '{book.title}' returned successfully.", 'success')
        
    return redirect(request.referrer or url_for('main.admin_dashboard'))

@main.route("/admin/approve/<int:borrow_id>", methods=['POST'])
@login_required
@admin_required
def approve_request(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)
    if borrow_record.status != 'pending':
        flash('This request is no longer pending.', 'warning')
        return redirect(url_for('main.admin_dashboard'))
    
    book = Book.query.get(borrow_record.book_id)
    if book.quantity > 0:
        borrow_record.status = 'approved'
        borrow_record.borrow_date = datetime.now(timezone.utc)
        borrow_record.return_date = datetime.now(timezone.utc) + timedelta(days=30)
        book.quantity -= 1
        db.session.commit()
        flash(f"Request for '{book.title}' approved successfully.", 'success')
    else:
        flash(f"Cannot approve request. '{book.title}' is currently out of stock.", 'danger')
    
    return redirect(url_for('main.admin_dashboard'))

@main.route("/admin/reject/<int:borrow_id>", methods=['POST'])
@login_required
@admin_required
def reject_request(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)
    if borrow_record.status != 'pending':
        flash('This request is no longer pending.', 'warning')
        return redirect(url_for('main.admin_dashboard'))
    
    borrow_record.status = 'rejected'
    db.session.commit()
    flash("Borrow request has been rejected.", 'info')
    return redirect(url_for('main.admin_dashboard'))

# Admin Routes
@main.route("/admin")
@main.route("/admin/borrowed_books")
@login_required
@admin_required
def admin_dashboard():
    books = Book.query.all()
    borrowed_books_list = BorrowedBook.query.all()
    
    total_books = sum(b.quantity for b in books)
    available_qty = sum(b.quantity for b in books)
    total_borrowed = BorrowedBook.query.filter(BorrowedBook.status == 'approved').count()
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
                "requested_at": record.requested_at.strftime('%Y-%m-%d %H:%M') if record.requested_at else 'N/A',
                "borrow_date": record.borrow_date.strftime('%Y-%m-%d') if record.borrow_date else 'N/A',
                "return_date": record.return_date.strftime('%Y-%m-%d') if record.return_date else 'N/A',
                "status": record.status
            })
    
    # We will need the AddBookForm to pass to template or we can just redirect to a separate add-book page.
    form = AddBookForm()
    
    return render_template("admin_dashboard.html",
                           books=books,
                           borrowed_books=borrowed_books,
                           total_books=total_books,
                           available_books=available_qty,
                           total_borrowed=total_borrowed,
                           total_users=total_users,
                           form=form)

@main.route("/admin/add_book", methods=['POST'])
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
                
    return redirect(url_for('main.admin_dashboard'))

@main.route("/admin/remove_book/<int:book_id>", methods=['POST'])
@login_required
@admin_required
def remove_book(book_id):
    book = Book.query.get_or_404(book_id)
    # Check if currently borrowed (approved and not returned)
    active_borrows = BorrowedBook.query.filter_by(book_id=book.id).filter(BorrowedBook.status == 'approved').count()
    if active_borrows > 0:
        flash(f'Cannot remove book "{book.title}" because it is currently borrowed by {active_borrows} user(s).', 'warning')
    else:
        # Delete borrow history for this book to avoid foreign key constraints errors
        BorrowedBook.query.filter_by(book_id=book.id).delete()
        db.session.delete(book)
        db.session.commit()
        flash('Book removed successfully!', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route("/admin/send_reminder/<int:borrow_id>", methods=['POST', 'GET'])
@login_required
@admin_required
def send_reminder(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)
    user = User.query.get(borrow_record.user_id)
    book = Book.query.get(borrow_record.book_id)
    
    if user and book:
        # For this prototype we will just flash a message representing an email sent.
        flash(f"Reminder email sent to {user.email} for '{book.title}'.", 'info')
    
    return redirect(url_for('main.admin_dashboard'))
