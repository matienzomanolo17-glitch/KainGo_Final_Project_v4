import smtplib
import threading
from email.message import EmailMessage
from config import Config


def _send(to, subject, body):
    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        print(f"\n[EMAIL not configured - printing instead]\nTo: {to}\nSubject: {subject}\n{body}\n")
        return
    msg = EmailMessage()
    msg["From"] = f"{Config.BRAND} <{Config.MAIL_USERNAME}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:  # never crash the website because of email
        print("Email failed:", e)


def send_email(to, subject, body):
    """Sends in the background so the page does not wait for the mail server."""
    threading.Thread(target=_send, args=(to, subject, body), daemon=True).start()
