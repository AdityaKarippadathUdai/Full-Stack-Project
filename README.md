# 📚 Library Management System (Flask + PostgreSQL)

## 🚀 Project Overview

The **Library Management System** is a full‑stack web application built with **Flask** that simplifies book management, user handling, and borrowing workflows.  
It uses a **request‑based borrowing system**:

- Users request books.
- Admin approves/rejects requests.
- Admin manages returns and reminders.

The system features a clean UI (Bootstrap + jQuery), secure authentication, role‑based access control, and automated email reminders.

---

## ✨ Features

### 👤 User Features
- Register and log in securely.
- Browse available books by category.
- Request books (no direct borrowing).
- View their issued books and return dates.

### 🛠️ Admin Features
- Admin dashboard with overview.
- Add / delete books; upload book images.
- Approve / reject borrow requests.
- Mark books as returned.
- Remove users.
- Manually send reminder emails.
- View all borrowing activity.

### 🔔 Reminder System
- Automatic reminders sent **30 days** after approval.
- Runs in background using **APScheduler**.
- Only applies to approved requests with books not yet returned.

### 🌙 UI Features
- Responsive design with Bootstrap.
- Dark mode toggle.
- Card‑based book layout.
- Pagination (16 books per page).

---

## 🏗️ Tech Stack

### 🔹 Frontend
- HTML5
- Bootstrap 5
- JavaScript + jQuery

### 🔹 Backend
- Flask
- Flask‑SQLAlchemy (ORM)
- Flask‑Login (authentication)
- Flask‑Mail (email)
- Flask‑WTF (forms)
- Flask‑Bcrypt (password hashing)

### 🔹 Database
- PostgreSQL (production)
- SQLite (local development)

### 🔹 Other Tools
- APScheduler (background jobs)
- Gunicorn (production server)
- python‑dotenv (environment variables)

---

## 📁 Project Structure

Below is the complete directory structure of the project (based on the actual layout):

```text
project/
│
├── static/                           # Static files (served directly by web server)
│   ├── css/                          # Stylesheets
│   │   ├── main.css                  # Custom CSS
│   │   ├── dark-mode.css             # Dark mode styles
│   │   └── responsive.css            # Mobile/responsive overrides
│   ├── js/                           # JavaScript files
│   │   ├── main.js                   # Global scripts
│   │   ├── borrow.js                 # Borrowing workflow logic
│   │   └── dark-mode.js              # Dark mode toggle script
│   ├── images/                       # Uploaded book covers and static images
│   │   ├── default-cover.jpg         # Fallback image for books
│   │   └── logo.png                  # Website logo
│   └── fonts/                        # Custom fonts (if any)
│
├── templates/                        # Jinja2 HTML templates
│   ├── base.html                     # Base layout with navbar, footer, meta tags
│   ├── index.html                    # Homepage
│   ├── books.html                    # Browse books (with pagination)
│   ├── book_detail.html              # Single book view
│   ├── dashboard.html                # Admin dashboard
│   ├── requests.html                 # Pending borrow requests (admin)
│   ├── my_books.html                 # User's issued books
│   ├── login.html                    # Login page
│   ├── register.html                 # Registration page
│   ├── profile.html                  # User profile
│   ├── add_book.html                 # Form for adding a new book (admin)
│   ├── edit_book.html                # Edit book details (admin)
│   └── send_reminder.html            # Manual reminder form (admin)
│
├── app.py                            # Main Flask application factory and entry point
├── routes.py                         # All route definitions (blueprint)
├── models.py                         # SQLAlchemy ORM models (User, Book, BorrowedBook)
├── forms.py                          # WTForms classes for login, registration, add/edit book
├── extensions.py                     # Initialization of extensions (db, login_manager, mail)
├── config.py                         # Configuration classes (Development, Production, Testing)
├── scheduler.py                      # APScheduler configuration and reminder job
├── requirements.txt                  # Python dependencies with versions
├── .python-version                   # File for Render (e.g., "3.12")
├── .env                              # Environment variables (not committed)
├── .env.example                      # Example environment variables (committed)
├── .gitignore                        # Git ignore rules (venv, __pycache__, .env, etc.)
├── migrations/                       # Alembic database migrations (if using)
│   ├── versions/                     # Migration scripts
│   └── alembic.ini
├── tests/                            # Unit and integration tests
│   ├── test_models.py
│   ├── test_routes.py
│   └── conftest.py
├── wsgi.py                           # WSGI entry point for production (if separate)
├── Procfile                          # For Heroku/Render (optional)
└── README.md                         # This file
```

The `.python-version` file is used by Render to select the correct Python runtime.

---

## 🔐 Authentication & Authorization

- Passwords are hashed with **Flask‑Bcrypt**.
- Session management via **Flask‑Login**.
- Role‑based access:
  - **Admin**: full system control.
  - **User**: limited to requesting books and viewing their history.

---

## 🔄 Borrowing Workflow

1. User requests a book → request status = `Pending`.
2. Admin reviews requests:
   - **Approve** → book is issued, `borrow_date` is set.
   - **Reject** → request is closed.
3. On return, admin marks the book as `Returned`.

---

## 📊 Database Schema (Simplified)

### User
- `id` (PK)
- `name`
- `email`
- `password`
- `phone`
- `role`

### Book
- `id` (PK)
- `title`
- `author`
- `category`
- `image` (optional)

### BorrowedBook
- `id` (PK)
- `user_id` (FK)
- `book_id` (FK)
- `requested_at` (datetime)
- `borrow_date` (datetime, nullable)
- `return_date` (datetime, nullable)
- `status` (enum: `pending`, `approved`, `rejected`, `returned`)

---

## ⚙️ Local Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/library-management.git
cd library-management
```

### 2️⃣ Create and activate a virtual environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set up environment variables

Create a `.env` file in the project root with the following (adjust as needed):

```text
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://username:password@localhost/library_db  # or sqlite:///library.db
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Note:** For local development, you can use SQLite: `DATABASE_URL=sqlite:///library.db`.

### 5️⃣ Initialize the database

```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
...     # optionally create an admin user
...
```

### 6️⃣ Run the application

```bash
python app.py
```

The app will be available at `http://127.0.0.1:5000`.

---

## 🌍 Deployment on Render

### Prerequisites
- A GitHub repository with your code.
- A PostgreSQL database (Render provides a free tier).

### Steps
1. Push your code to GitHub.
2. Create a new **Web Service** on Render:
   - Connect your repository.
   - Set the **Environment** to **Python 3**.
   - Specify the **Python version** (very important!):
     - Add a file named `.python-version` in the root of your repo with content:
       ```text
       3.12
       ```
     - This tells Render to use Python 3.12 instead of the default (which may be newer and cause compatibility issues).
3. Configure build & start commands:
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app
     ```
4. Set environment variables in the Render dashboard:
   - `SECRET_KEY`
   - `DATABASE_URL` (use the internal connection string from your Render PostgreSQL instance)
   - `MAIL_USERNAME`
   - `MAIL_PASSWORD`
   - `MAIL_DEFAULT_SENDER`
   - (Any other required config)
5. Deploy – Render will automatically build and run your app.

### Verifying Python Version
During the build, check the logs for a line like:

```text
=> Using Python 3.12.x
```

If you see `3.14`, double‑check the `.python-version` file and ensure it’s committed and present in the root.

---

## 🐞 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| SQLAlchemy error with Python 3.14 | Use `.python-version` to lock to 3.12. |
| Port not detected on Render | Make sure your app listens on `0.0.0.0` and uses the `PORT` environment variable. |
| Pagination not working | Verify that backend pagination logic and URL parameters are correctly implemented. |
| Background scheduler not running | Ensure APScheduler is started inside the application context, and use a production‑safe scheduler (e.g., `BackgroundScheduler`). |
| Email reminders not sending | Check that email credentials are correct and that the scheduler is active. |

---

## 📌 Future Improvements
- Search functionality.
- Book recommendations.
- Fine/penalty system for overdue books.
- Notifications dashboard.
- REST API for third‑party integrations.

---

## 👨‍💻 Author

**Aditya K U**  
B.Tech CSE-AI  
Amrita University

---

## ⭐ Acknowledgements

- Flask documentation
- Bootstrap framework
- Open‑source community

---

## 📜 License

This project is for academic and learning purposes.