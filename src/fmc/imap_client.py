import imaplib, email, re
from email.header import decode_header
from contextlib import contextmanager
from typing import Iterable, Sequence, Iterator

def decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for chunk, enc in parts:
        out.append(chunk.decode(enc or "utf-8", errors="replace") if isinstance(chunk, bytes) else chunk)
    return "".join(out)

_UID_RE = re.compile(rb'UID\s+(\d+)')

def _parse_uid_from_resp(resp: bytes) -> str | None:
    # resp example: b'123 (UID 456 BODY[HEADER.FIELDS ...]'
    m = _UID_RE.search(resp)
    return m.group(1).decode() if m else None

class IMAPClient:
    def __init__(self, host: str, user: str, password: str, folder: str = "INBOX", timeout: float = 15.0):
        self.host = host
        self.user = user
        self.password = password
        self.folder = folder
        self.timeout = timeout
        self.conn: imaplib.IMAP4_SSL | None = None

    @contextmanager
    def connect(self):
        self.conn = imaplib.IMAP4_SSL(self.host, timeout=self.timeout)
        if hasattr(self.conn, "sock") and self.conn.sock:
            try:
                self.conn.sock.settimeout(self.timeout)
            except Exception:
                pass
        self.conn.login(self.user, self.password)
        typ, _ = self.conn.select(self.folder, readonly=True)
        if typ != "OK":
            raise RuntimeError(f"Could not select folder {self.folder!r}")
        try:
            yield self
        finally:
            try:
                self.conn.logout()
            except Exception:
                pass

    def search_uids(self, criteria: str = "ALL") -> list[str]:
        assert self.conn
        typ, data = self.conn.uid("SEARCH", None, criteria)
        if typ != "OK" or not data or not data[0]:
            return []
        return [u.decode() for u in data[0].split()]

    def fetch_headers_stream(
        self,
        header_names: Sequence[str] = ("FROM", "SUBJECT", "DATE"),
        uids: list[str] | None = None,
        processed_uids: set[str] | None = None,
        limit: int | None = None,
        chunk_size: int = 300,
    ) -> Iterator[tuple[str, dict[str, str]]]:
        """
        Yields (uid, {Header: value, ...}) in batches to avoid timeouts/memory spikes.
        """
        assert self.conn, "Use within `with self.connect():`"
        processed_uids = processed_uids or set()

        if uids is None:
            uids = self.search_uids("ALL")
        if limit is not None:
            uids = uids[:limit]

        # Prepare header field list once
        field_list = " ".join(header_names)

        for i in range(0, len(uids), chunk_size):
            chunk = [u for u in uids[i:i+chunk_size] if u not in processed_uids]
            if not chunk:
                continue

            # Comma-separated UID set per RFC
            uid_set = ",".join(chunk).encode()

            typ, msg_data = self.conn.uid(
                "FETCH",
                uid_set,
                f"(BODY.PEEK[HEADER.FIELDS ({field_list})])"
            )
            if typ != "OK" or not msg_data:
                # Optional: fallback to full RFC822.HEADER per chunk
                typ, msg_data = self.conn.uid("FETCH", uid_set, "(RFC822.HEADER)")
                if typ != "OK" or not msg_data:
                    continue

            # msg_data is a list of parts; tuples have (resp, raw_bytes)
            for part in msg_data:
                if not isinstance(part, tuple) or len(part) < 2:
                    continue
                resp_line, raw = part
                uid = _parse_uid_from_resp(resp_line)
                if not uid:
                    # If UID not present (some servers), skip or parse seqnum
                    continue

                msg = email.message_from_bytes(raw)
                record: dict[str, str] = {}
                for name in header_names:
                    pretty = name.title() if name.isupper() else name
                    record[pretty] = decode_header_value(msg.get(pretty))
                yield uid, record
