import imaplib
import email
from email.header import decode_header
import os
import csv

# --- CONFIGURATION ---
IMAP_SERVER = "imap.example.com"
EMAIL_ACCOUNT = "user@example.com"
PASSWORD = "your_password"  # ideally use getpass() or a config file
SAVE_DIR = "saved_emails"
CSV_LOG = "saved_emails.csv"

# --- CONNECT TO IMAP ---
def connect():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")
    return mail

# --- FETCH EMAIL HEADERS ---
def fetch_email_headers(mail):
    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()
    headers = []
    for eid in email_ids:
        result, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        subject, encoding = decode_header(msg.get("Subject"))[0]
        subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject
        sender = msg.get("From")
        headers.append((eid, subject, sender))
    return headers

# --- SIMPLE USER PROMPT ---
def user_select(headers):
    selected = []
    for eid, subject, sender in headers:
        print(f"\nFrom: {sender}\nSubject: {subject}")
        keep = input("Save this email? (y/n): ").lower()
        if keep == "y":
            selected.append(eid)
    return selected

# --- SAVE EMAILS TO DISK + LOG ---
def save_emails(mail, selected_ids):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(CSV_LOG, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Subject", "From"])

        for eid in selected_ids:
            result, msg_data = mail.fetch(eid, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject, encoding = decode_header(msg.get("Subject"))[0]
            subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject
            sender = msg.get("From")

            filename = f"{eid.decode()}.eml"
            with open(os.path.join(SAVE_DIR, filename), "wb") as eml_file:
                eml_file.write(raw_email)

            writer.writerow([filename, subject, sender])

# --- MAIN EXECUTION ---
def main():
    mail = connect()
    headers = fetch_email_headers(mail)
    selected_ids = user_select(headers)
    save_emails(mail, selected_ids)
    mail.logout()

if __name__ == "__main__":
    main()