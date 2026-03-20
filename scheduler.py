"""
scheduler.py — Automatic overdue book reminder job.

Runs every 6 hours via APScheduler.
Sends reminders for approved books where borrow_date > 30 days ago
and no reminder has been sent in the last 7 days.
"""
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


def send_auto_reminders(app):
    """Background job: find overdue books and notify borrowers."""
    with app.app_context():
        try:
            from extensions import db, mail
            from models import BorrowedBook, Notification
            from sqlalchemy import and_, or_

            now       = datetime.now(timezone.utc)
            cutoff    = now - timedelta(days=30)   # borrow must be this old
            re_notify = now - timedelta(days=7)    # min gap between reminders

            # Find qualifying records
            records = BorrowedBook.query.filter(
                BorrowedBook.status == 'approved',
                BorrowedBook.borrow_date != None,
                BorrowedBook.borrow_date < cutoff,
                or_(
                    BorrowedBook.last_reminder_at == None,
                    BorrowedBook.last_reminder_at < re_notify
                )
            ).all()

            logger.info(f"[Scheduler] Auto-reminder check: {len(records)} eligible records.")

            for record in records:
                try:
                    _send_one_reminder(app, record, now)
                except Exception as e:
                    logger.error(f"[Scheduler] Failed for borrow_id={record.id}: {e}")
                    db.session.rollback()

        except Exception as e:
            logger.error(f"[Scheduler] Job error: {e}")


def _send_one_reminder(app, record, now):
    from extensions import db, mail
    from models import User, Book, Notification
    from flask_mail import Message as MailMessage

    user = User.query.get(record.user_id)
    book = Book.query.get(record.book_id)

    if not (user and book):
        return

    # --- Build status message ---
    return_dt = record.return_date
    if return_dt:
        # Ensure timezone-aware
        if return_dt.tzinfo is None:
            return_dt = return_dt.replace(tzinfo=timezone.utc)
        days_left = (return_dt - now).days

        if days_left < 0:
            status_msg   = f"This book is OVERDUE by {abs(days_left)} day(s). Please return it immediately."
            subject_tag  = "OVERDUE"
            status_html  = f"<strong style='color:#c0392b'>⚠ Overdue by {abs(days_left)} day(s).</strong> Please return it immediately."
        elif days_left <= 3:
            status_msg   = f"This book is due in {days_left} day(s). Please arrange to return it soon."
            subject_tag  = "Due Soon"
            status_html  = f"<strong style='color:#e67e22'>Due in {days_left} day(s).</strong> Please arrange to return it soon."
        else:
            status_msg   = f"This book is due on {return_dt.strftime('%d %b %Y')}."
            subject_tag  = "Reminder"
            status_html  = f"This book is due on <strong>{return_dt.strftime('%d %b %Y')}</strong>."

        return_date_str = return_dt.strftime('%d %b %Y')
    else:
        status_msg     = "Please return the book at your earliest convenience."
        subject_tag    = "Reminder"
        status_html    = "Please return the book at your earliest convenience."
        return_date_str = "N/A"

    notification_text = f"[Auto-Reminder] '{book.title}' — {status_msg}"

    # 1. In-app notification
    notif = Notification(user_id=user.id, message=notification_text)
    db.session.add(notif)

    # 2. Update timestamp + count (idempotency)
    record.last_reminder_at = now
    record.reminder_count   = (record.reminder_count or 0) + 1
    db.session.commit()

    logger.info(f"[Scheduler] In-app notification created for user={user.id}, book={book.id}.")

    # 3. Email (best-effort)
    if app.config.get('MAIL_USERNAME'):
        try:
            html_body = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;
                        border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
              <div style="background:#2c3e50;padding:20px;text-align:center">
                <h2 style="color:#f4d03f;margin:0">📚 Smart Library</h2>
                <p style="color:#aab8c8;margin:6px 0 0">Automated Book Return Reminder</p>
              </div>
              <div style="padding:30px">
                <p style="font-size:16px">Hello <strong>{user.name}</strong>,</p>
                <p>This is an automated reminder about a book you have borrowed.</p>
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
                <p style="background:#fff3cd;border-left:4px solid #f4d03f;
                           padding:12px;border-radius:4px">
                  {status_html}
                </p>
                <p style="color:#6c757d;font-size:13px">
                  This message was sent automatically. If you have already returned this book,
                  please disregard it.
                </p>
              </div>
              <div style="background:#f8f9fa;padding:15px;text-align:center;
                          color:#aaa;font-size:12px">
                Smart Library — Automated Reminder System
              </div>
            </div>
            """
            msg = MailMessage(
                subject=f"[Smart Library – {subject_tag}] Return reminder for '{book.title}'",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            logger.info(f"[Scheduler] Email sent to {user.email} for book '{book.title}'.")
        except Exception as e:
            logger.error(f"[Scheduler] Email failed for {user.email}: {e}")
