"""Minimal Flask app used only to preview the Library Management System templates."""
from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = "preview-only"

# Sample data for template preview
SAMPLE_BOOKS = [
    {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "isbn": "978-0-262-03384-8", "available": True, "quantity": 5},
    {"title": "Clean Code", "author": "Robert C. Martin", "isbn": "978-0-132-35088-4", "available": True, "quantity": 3},
    {"title": "Design Patterns", "author": "Erich Gamma et al.", "isbn": "978-0-201-63361-0", "available": False, "quantity": 2},
    {"title": "The Pragmatic Programmer", "author": "David Thomas", "isbn": "978-0-135-95705-9", "available": True, "quantity": 4},
    {"title": "Artificial Intelligence", "author": "Stuart Russell", "isbn": "978-0-134-61099-3", "available": True, "quantity": 6},
    {"title": "Structure & Interpretation", "author": "Harold Abelson", "isbn": "978-0-262-51087-5", "available": False, "quantity": 1},
    {"title": "Computer Networking", "author": "James Kurose", "isbn": "978-0-133-59414-0", "available": True, "quantity": 7},
    {"title": "Operating System Concepts", "author": "Abraham Silberschatz", "isbn": "978-1-119-32091-3", "available": True, "quantity": 4},
]

SAMPLE_ISSUED = [
    {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "issue_date": "2026-02-15", "return_date": "2026-03-15", "status": "active"},
    {"title": "Clean Code", "author": "Robert C. Martin", "issue_date": "2026-01-10", "return_date": "2026-02-10", "status": "overdue"},
    {"title": "Design Patterns", "author": "Erich Gamma et al.", "issue_date": "2026-01-05", "return_date": "2026-02-05", "status": "returned"},
    {"title": "The Pragmatic Programmer", "author": "David Thomas", "issue_date": "2026-03-01", "return_date": "2026-04-01", "status": "active"},
    {"title": "Refactoring", "author": "Martin Fowler", "issue_date": "2025-12-20", "return_date": "2026-01-20", "status": "returned"},
]

SAMPLE_BORROWED = [
    {"user_name": "Alice Johnson", "book_title": "Introduction to Algorithms", "issue_date": "2026-02-10", "due_date": "2026-03-10", "status": "overdue"},
    {"user_name": "Bob Williams", "book_title": "Clean Code", "issue_date": "2026-02-20", "due_date": "2026-03-20", "status": "active"},
    {"user_name": "Carol Davis", "book_title": "Design Patterns", "issue_date": "2026-01-15", "due_date": "2026-02-15", "status": "overdue"},
    {"user_name": "David Lee", "book_title": "The Pragmatic Programmer", "issue_date": "2026-03-01", "due_date": "2026-04-01", "status": "active"},
]

@app.route("/")
def index():
    return render_template("index.html", books=SAMPLE_BOOKS)

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html",
                           user={"name": "John Doe", "books_issued": 3, "books_returned": 12, "overdue": 1},
                           issued_books=SAMPLE_ISSUED,
                           books=SAMPLE_BOOKS)


@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html",
                           books=SAMPLE_BOOKS,
                           borrowed_books=SAMPLE_BORROWED,
                           total_books="1,245",
                           total_issued="328",
                           total_overdue="17")

@app.route("/success")
def success():
    return render_template("success.html",
                           title="Book Borrowed Successfully!",
                           message="You have successfully borrowed 'Introduction to Algorithms'. Please return it by March 15, 2026.")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
