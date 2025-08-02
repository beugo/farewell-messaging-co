import imaplib
import email
from email.header import decode_header
import os
import csv
import argparse
import getpass
import time

# --- CONFIGURATION ---
IMAP_SERVER = "imap.themessagingco.com.au"
SAVE_DIR = "saved_emails"
DELETE_DIR = "discarded_emails"
CSV_LOG = "saved_emails.csv"
SENDERS_LOG = "saved_senders.txt"
PROCESSED_IDS_LOG = "processed_ids.txt"

undo_stack = []
saved_senders = set()
processed_ids = set()

# --- INITIAL SETUP ---
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(DELETE_DIR, exist_ok=True)

if os.path.exists(SENDERS_LOG):
    with open(SENDERS_LOG, "r") as f:
        saved_senders.update(line.strip() for line in f)

if os.path.exists(PROCESSED_IDS_LOG):
    with open(PROCESSED_IDS_LOG, "r") as f:
        processed_ids.update(line.strip() for line in f)

def connect(email_addr, password):
    print("Connecting to IMAP server...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    print("Logging in...")
    mail.login(email_addr, password)
    print("Selecting inbox...")
    mail.select("inbox")
    print("✅ Connected and inbox selected.")
    return mail

def fetch_email_headers(mail):
    print("Fetching email list...")
    try:
        mail.sock.settimeout(10)
        result, data = mail.search(None, "ALL")
    except Exception as e:
        print(f"❌ Failed to fetch email list: {e}")
        return []

    if result != "OK":
        print("❌ IMAP search failed.")
        return []

    email_ids = data[0].split()
    print(f"✅ Found {len(email_ids)} emails.")
    email_ids = email_ids[:10]
    headers = []
    for eid in email_ids:
        eid_str = eid.decode()
        if eid_str in processed_ids:
            continue
        result, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject_raw = msg.get("Subject")
        if subject_raw is None:
            subject = "(No Subject)"
        else:
            subject, encoding = decode_header(subject_raw)[0]
            subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject

        sender = msg.get("From") or "(Unknown Sender)"
        headers.append((eid, subject, sender))
    return headers

def get_email_preview(mail, eid):
    result, msg_data = mail.fetch(eid, "(RFC822)")
    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    # Get plain text version
    preview = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "").lower()
            if content_type == "text/plain" and "attachment" not in disposition:
                try:
                    preview = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                except:
                    preview = "[Could not decode preview]"
                break
    else:
        try:
            preview = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        except:
            preview = "[Could not decode preview]"

    return preview.strip()[:1000]

def save_email(mail, eid, subject, sender, folder):
    result, msg_data = mail.fetch(eid, "(RFC822)")
    raw_email = msg_data[0][1]
    filename = f"{eid.decode()}.eml"
    with open(os.path.join(folder, filename), "wb") as f:
        f.write(raw_email)
    return filename

def log_email(filename, subject, sender):
    with open(CSV_LOG, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([filename, subject, sender])

def save_sender(sender):
    if sender in saved_senders:
        print(f"[!] Sender '{sender}' already saved.")
    else:
        saved_senders.add(sender)
        with open(SENDERS_LOG, "a") as f:
            f.write(sender + "\n")
        print(f"[+] Saved sender: {sender}")

def mark_processed(eid):
    with open(PROCESSED_IDS_LOG, "a") as f:
        f.write(eid.decode() + "\n")
    processed_ids.add(eid.decode())

def user_select(mail, headers):
    print("\nControls: l = Discard, r = Save, u = Undo, s = Save sender, p = Preview email\n")
    selected_ids = []
    i = 0
    while i < len(headers):
        eid, subject, sender = headers[i]
        print(f"\nEmail {i+1}/{len(headers)}\nFrom: {sender}\nSubject: {subject}\n")

        while True:
            choice = input("Choice (l/r/s/u/p): ").strip().lower()
            if choice == "l":
                filename = save_email(mail, eid, subject, sender, DELETE_DIR)
                undo_stack.append(("discard", eid, filename, subject, sender))
                mark_processed(eid)
                print("→ Discarded.")
                break
            elif choice == "r":
                filename = save_email(mail, eid, subject, sender, SAVE_DIR)
                log_email(filename, subject, sender)
                undo_stack.append(("save", eid, filename, subject, sender))
                selected_ids.append(eid)
                mark_processed(eid)
                print("→ Saved.")
                break
            elif choice == "u":
                if not undo_stack:
                    print("[!] Nothing to undo.")
                else:
                    action, eid, filename, subject, sender = undo_stack.pop()
                    folder = SAVE_DIR if action == "save" else DELETE_DIR
                    path = os.path.join(folder, filename)
                    if os.path.exists(path):
                        os.remove(path)
                    if action == "save" and eid in selected_ids:
                        selected_ids.remove(eid)
                    processed_ids.discard(eid.decode())
                    with open(PROCESSED_IDS_LOG, "w") as f:
                        for pid in processed_ids:
                            f.write(pid + "\n")
                    print("↩ Undo complete.")
            elif choice == "s":
                save_sender(sender)
            elif choice == "p":
                print("\n📨 Email Preview:\n" + "-"*40)
                print(get_email_preview(mail, eid))
                print("-"*40)
            else:
                print("Invalid choice. Use l, r, s, or u.")

        i += 1

    return selected_ids

def main():
    parser = argparse.ArgumentParser(description="IMAP Email Picker")
    parser.add_argument("--email", required=True, help="Your email address")
    args = parser.parse_args()
    password = getpass.getpass("Enter your email password: ")

    mail = connect(args.email, password)

    if not os.path.exists(CSV_LOG):
        with open(CSV_LOG, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Filename", "Subject", "From"])

    headers = fetch_email_headers(mail)
    if not headers:
        print("🎉 All emails have already been processed.")
    else:
        print("Getting emails ready for processing...")
        user_select(mail, headers)

    mail.logout()
    print("\n✅ Done.")

if __name__ == "__main__":
    main()
