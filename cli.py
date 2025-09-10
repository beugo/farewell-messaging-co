import getpass, os, yaml
from dotenv import load_dotenv

from src.fmc.imap_client import IMAPClient
from src.fmc.collator import Collator

def main():
    load_dotenv()
    password = getpass.getpass("Give me your email password hee hee hee: ")

    client = IMAPClient(
        host=os.getenv("IMAP_SERVER", ""),
        user=os.getenv("IMAP_USER", ""),
        password=password,
        folder="INBOX"
    )

    collator = Collator(client)

    senders = collator.build_sender_index()

    with open("detailed_senders.txt", "w") as f:
        yaml.safe_dump(senders, f)

    with open("senders.txt", "w") as f:
        yaml.safe_dump(list(senders.keys()), f)

if __name__ == "__main__":
    main()
