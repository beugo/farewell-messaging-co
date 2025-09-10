from collections import defaultdict
from .imap_client import IMAPClient
from typing import Dict, List

class Collator:
    def __init__(self, client: IMAPClient):
        self.client = client

    def build_sender_index(self, limit: int | None = None) -> dict[str, dict]:
        """
        Returns:
          {
            "sender@domain": {
              "count": int,
              "uids": [uid, ...],
              "examples": [{"subject": str, "date": str}, ... up to 3]
            },
            ...
          }
        """
        index: Dict[str, dict] = defaultdict(lambda: {"count": 0, "uids": [], "examples": []})

        with self.client.connect():
            for uid, headers in self.client.fetch_headers_stream(
                header_names=("FROM", "SUBJECT", "DATE"),
                limit=limit,
                chunk_size=300,
            ):
                sender = headers.get("From", "") or ""
                subj = headers.get("Subject", "") or ""
                date = headers.get("Date", "") or ""

                bucket = index[sender]
                bucket["count"] += 1
                bucket["uids"].append(uid)
                if len(bucket["examples"]) < 3:
                    bucket["examples"].append({"subject": subj, "date": date})

        return dict(index)
