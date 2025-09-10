import imaplib
import email
from email.header import decode_header
from contextlib import contextmanager
from typing import Iterable

class IMAPClient:
    def __init__(self, host: str, user: str, password: str, folder: str = "INBOX"):
        self.host = host
        self.user = user
        self.password = password
        self.folder = folder
        self.conn: imaplib.IMAP4_SSL | None = None

    @contextmanager
    def connect(self):
        self.conn = imaplib.IMAP4_SSL(self.host)
        self.conn.login(self.user, self.password)
        try:
            yield self
        finally:
            try:
                self.conn.logout()
            except Exception:
                pass

    def iter_message_uids(self) -> Iterable[str]:
        assert self.conn
        typ, _ = self.conn.select(self.folder, readonly=True)
        if typ != "OK":
            return
        typ, data = self.conn.uid("SEARCH", None, "ALL")
        if typ != "OK" or not data or not data[0]:
            return
        for uid in data[0].split():
            yield uid.decode()

    def fetch_headers(self, uid: str) -> dict[str, str]:
        assert self.conn
        typ, data = self.conn.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        if typ != "OK" or not data or not data[0]:
            return {}
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        headers = {k: v for k, v in msg.items()}
        for k, v in list(headers.items()):
            parts = decode_header(v)
            decoded = "".join(
                (p.decode(enc or "utf-8", errors="replace") if isinstance(p, bytes) else p)
                for p, enc in parts
            )
            headers[k] = decoded
        return headers
