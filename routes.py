from flask import render_template, url_for, flash, redirect, request, abort, Blueprint, current_app
from flask_login import login_user, current_user, logout_user, login_required
from extensions import db, bcrypt, login_manager, mail
from models import User, Book, BorrowedBook, Notification
from forms import RegisterForm, LoginForm, AddBookForm, BorrowBookForm
from flask_mail import Message as MailMessage
from datetime import datetime, timedelta, timezone
import os
import secrets

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

    # Unread notifications for the dashboard panel (latest 5)
    recent_notifications = Notification.query\
        .filter_by(user_id=current_user.id, is_read=False)\
        .order_by(Notification.created_at.desc())\
        .limit(5).all()
    
    user_stats = {
        "name": current_user.name,
        "books_borrowed": len([b for b in borrowed_books if b.status == 'approved']),
        "books_returned": len([b for b in borrowed_books if b.status == 'returned']),
        "overdue": 0 # feature removed in db simplification
    }
    
    books = Book.query.all()
    return render_template(
        "dashboard.html",
        user=user_stats,
        borrowed_books=borrowed_books,
        books=books,
        recent_notifications=recent_notifications
    )

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
                "status": record.status,
                "last_reminder_at": record.last_reminder_at.strftime('%Y-%m-%d %H:%M') if record.last_reminder_at else 'Never'
            })
    
    # All users (exclude admins for the manage-users table)
    all_users = User.query.filter_by(role='user').order_by(User.name).all()

    # Annotate each user with their active borrow count
    users_data = []
    for u in all_users:
        active = BorrowedBook.query.filter_by(user_id=u.id, status='approved').count()
        total  = BorrowedBook.query.filter_by(user_id=u.id).count()
        users_data.append({
            'id':      u.id,
            'name':    u.name,
            'email':   u.email,
            'phone':   u.phone,
            'role':    u.role,
            'active':  active,
            'total':   total,
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
                           users_data=users_data,
                           form=form)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/images', picture_fn)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    form_picture.save(picture_path)
    return picture_fn

@main.route("/admin/add_book", methods=['POST'])
@login_required
@admin_required
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        image_file = 'default.jpg'
        if form.image.data:
            image_file = save_picture(form.image.data)
            
        book = Book(title=form.title.data, 
                    author=form.author.data, 
                    isbn=form.isbn.data, 
                    category=form.category.data, 
                    quantity=form.quantity.data,
                    image_file=image_file)
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


@main.route("/admin/remove_user/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def remove_user(user_id):
    """Safely remove a regular user. Blocked if they have active borrowed books."""
    target = User.query.get_or_404(user_id)

    # Guard: cannot delete yourself
    if target.id == current_user.id:
        flash("You cannot remove your own account.", 'danger')
        return redirect(url_for('main.admin_dashboard') + '#manageUsersSection')

    # Guard: cannot delete another admin
    if target.role == 'admin':
        flash("Admin accounts cannot be removed.", 'danger')
        return redirect(url_for('main.admin_dashboard') + '#manageUsersSection')

    # Guard: block if user has active (approved, not returned) loans
    active_loans = BorrowedBook.query.filter_by(
        user_id=target.id, status='approved'
    ).count()
    if active_loans > 0:
        flash(
            f'Cannot remove "{target.name}" — they currently have {active_loans} '
            f'active borrowed book(s). Ask them to return the book(s) first.',
            'warning'
        )
        return redirect(url_for('main.admin_dashboard') + '#manageUsersSection')

    # Safe to delete: clean up related data first
    # 1. Delete all borrow records (pending / rejected / returned only at this point)
    BorrowedBook.query.filter_by(user_id=target.id).delete()
    # 2. Delete all notifications
    Notification.query.filter_by(user_id=target.id).delete()
    # 3. Delete the user
    db.session.delete(target)
    db.session.commit()

    flash(f'User "{target.name}" has been removed successfully.', 'success')
    return redirect(url_for('main.admin_dashboard') + '#manageUsersSection')

@main.route("/admin/send_reminder/<int:borrow_id>", methods=['POST', 'GET'])
@login_required
@admin_required
def send_reminder(borrow_id):
    borrow_record = BorrowedBook.query.get_or_404(borrow_id)

    if borrow_record.status != 'approved':
        flash('Reminders can only be sent for approved books.', 'warning')
        return redirect(url_for('main.admin_dashboard'))

    user = User.query.get(borrow_record.user_id)
    book = Book.query.get(borrow_record.book_id)

    if not (user and book):
        flash("Could not send reminder. User or Book not found.", "danger")
        return redirect(url_for('main.admin_dashboard'))

    # --- Build contextual message ---
    now = datetime.now(timezone.utc)
    return_dt = borrow_record.return_date
    if return_dt:
        # Make return_dt timezone-aware if it isn't
        if return_dt.tzinfo is None:
            from datetime import timezone as _tz
            return_dt = return_dt.replace(tzinfo=_tz.utc)
        days_left = (return_dt - now).days
        if days_left < 0:
            status_msg = f"This book is <strong>overdue by {abs(days_left)} day(s)</strong>. Please return it immediately."
            subject_tag = "OVERDUE"
        elif days_left <= 3:
            status_msg = f"This book is <strong>due in {days_left} day(s)</strong>. Please arrange to return it soon."
            subject_tag = "Due Soon"
        else:
            status_msg = f"This book is due on <strong>{return_dt.strftime('%d %b %Y')}</strong>."
            subject_tag = "Reminder"
        return_date_str = return_dt.strftime('%d %b %Y')
    else:
        status_msg = "Please return the book at your earliest convenience."
        subject_tag = "Reminder"
        return_date_str = "N/A"

    notification_text = (
        f"Library Reminder: '{book.title}' — return date {return_date_str}. "
        f"{status_msg.replace('<strong>', '').replace('</strong>', '')}"
    )

    # --- 1. In-App Notification ---
    notif = Notification(user_id=user.id, message=notification_text)
    db.session.add(notif)

    # --- 2. Update reminder timestamp + count ---
    borrow_record.last_reminder_at = now
    borrow_record.reminder_count   = (borrow_record.reminder_count or 0) + 1

    db.session.commit()

    # --- 3. Email Notification (best-effort) ---
    email_sent = False
    if current_app.config.get('MAIL_USERNAME'):
        try:
            html_body = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#2c3e50;padding:20px;text-align:center">
                <h2 style="color:#f4d03f;margin:0">📚 Smart Library</h2>
                <p style="color:#aab8c8;margin:6px 0 0">Book Return Reminder</p>
              </div>
              <div style="padding:30px">
                <p style="font-size:16px">Hello <strong>{user.name}</strong>,</p>
                <p>This is a reminder about a book you have borrowed from Smart Library.</p>
                <table style="width:100%;border-collapse:collapse;margin:20px 0">
                  <tr style="background:#f8f9fa">
                    <td style="padding:10px;font-weight:bold;width:40%">Book Title</td>
                    <td style="padding:10px">{book.title}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px;font-weight:bold">Author</td>
                    <td style="padding:10px">{book.author}</td>
                  </tr>
                  <tr style="background:#f8f9fa">
                    <td style="padding:10px;font-weight:bold">Return Date</td>
                    <td style="padding:10px">{return_date_str}</td>
                  </tr>
                </table>
                <p style="background:#fff3cd;border-left:4px solid #f4d03f;padding:12px;border-radius:4px">
                  {status_msg}
                </p>
                <p style="color:#6c757d;font-size:13px">If you have already returned this book, please disregard this message.</p>
              </div>
              <div style="background:#f8f9fa;padding:15px;text-align:center;color:#aaa;font-size:12px">
                Smart Library &mdash; Automated Reminder
              </div>
            </div>
            """
            msg = MailMessage(
                subject=f"[Smart Library – {subject_tag}] Return reminder for '{book.title}'",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            email_sent = True
        except Exception as e:
            current_app.logger.error(f"Reminder email failed for user {user.id}: {e}")

    if email_sent:
        flash(f"Reminder sent to {user.name} ({user.email}) successfully.", 'success')
    else:
        flash(f"In-app notification sent to {user.name}. (Configure MAIL_USERNAME in .env to also send email)", 'success')

    return redirect(url_for('main.admin_dashboard'))


# ===== User Notifications =====
@main.route("/notifications")
@login_required
def notifications():
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    user_notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    # Mark all as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('notifications.html', notifications=user_notifications)


@main.app_context_processor
def inject_notification_count():
    if current_user.is_authenticated and current_user.role == 'user':
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    else:
        count = 0
    return {'unread_notification_count': count}
