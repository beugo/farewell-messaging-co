# group_senders.py
from email.utils import parseaddr

PERSONAL_PROVIDERS = {
    "gmail.com","googlemail.com","outlook.com","hotmail.com","live.com","msn.com",
    "yahoo.com","ymail.com","rocketmail.com","icloud.com","me.com","mac.com",
    "proton.me","protonmail.com","aol.com","gmx.com","gmx.de","mail.com",
    "fastmail.com","yandex.ru","yandex.com","qq.com","163.com","hey.com","pm.me"
}

def canonical_email(s: str) -> str:
    """Extract address, lowercase, strip gmail +tags and dots."""
    _, addr = parseaddr(s)
    addr = (addr or "").strip().lower()
    if "@" not in addr:
        return ""
    local, dom = addr.split("@", 1)
    if dom in {"gmail.com","googlemail.com"}:
        if "+" in local:
            local = local.split("+", 1)[0]
        local = local.replace(".", "")
    return f"{local}@{dom}"

def is_company(addr: str) -> bool:
    if "@" not in addr: 
        return False
    dom = addr.split("@", 1)[1]
    return dom not in PERSONAL_PROVIDERS

def main(inp="senders.txt", outp="senders_grouped.txt"):
    # read all lines
    with open(inp, "r", encoding="utf-8") as f:
        raw = [line.strip() for line in f if line.strip()]

    # normalize + dedupe
    emails = []
    for s in raw:
        e = canonical_email(s)
        if e:
            emails.append(e)

    uniq = sorted(set(emails))
    companies = sorted([e for e in uniq if is_company(e)])
    others    = sorted([e for e in uniq if not is_company(e)])

    with open(outp, "w", encoding="utf-8") as f:
        f.write("=== Company emails (A–Z) ===\n")
        for e in companies:
            f.write(e + "\n")
        f.write(f"\n({len(companies)} total)\n\n")

        f.write("=== Others (free/personal) ===\n")
        for e in others:
            f.write(e + "\n")
        f.write(f"\n({len(others)} total)\n")

    print(f"Done. Companies: {len(companies)}, Others: {len(others)} -> {outp}")

if __name__ == "__main__":
    main()
