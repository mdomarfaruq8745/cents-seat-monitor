import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from bs4 import BeautifulSoup

URL = "https://testcisia.it/calendario.php?tolc=cents&l=gb&lingua=inglese"
STATE_PATH = Path("state.json")


def telegram_send(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    api = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode()
    req = Request(api, data=body, headers={"User-Agent": "CEnTS-GitHub-Monitor/1.0"})
    with urlopen(req, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError("Telegram API rejected the notification")


def fetch_calendar():
    req = Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (compatible; CEnTSSeatMonitor/1.0)",
        "Accept-Language": "en-GB,en;q=0.9",
    })
    with urlopen(req, timeout=30) as response:
        html = response.read()

    soup = BeautifulSoup(html, "html.parser")
    table = None
    for candidate in soup.find_all("table"):
        trs = candidate.find_all("tr")
        if not trs:
            continue
        header_text = " ".join(c.get_text(" ", strip=True).upper()
                               for c in trs[0].find_all(["th", "td"]))
        if "UNIVERSITY" in header_text and "SEATS" in header_text and "DATE" in header_text:
            table = candidate
            break
    if table is None:
        raise RuntimeError("CISIA calendar table not found; page layout may have changed.")

    trs = table.find_all("tr")
    headers = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)).strip().upper()
               for c in trs[0].find_all(["th", "td"])]

    def col(*words):
        for i, h in enumerate(headers):
            if any(w in h for w in words):
                return i
        return None

    idx = {
        "format": col("FORMAT"),
        "university": col("UNIVERSITY"),
        "region": col("REGION"),
        "city": col("CITY"),
        "deadline": col("BOOKINGS DEADLINE", "DEADLINE"),
        "seats": col("SEATS"),
        "state": col("STATE"),
        "date": col("DATE"),
    }
    required = ["format", "university", "city", "deadline", "seats", "state", "date"]
    if any(idx[k] is None for k in required):
        raise RuntimeError(f"Unexpected CISIA columns: {headers}")

    results = {}
    for tr in trs[1:]:
        cells = tr.find_all(["td", "th"])
        if not cells or max(idx[k] for k in required) >= len(cells):
            continue
        row = {k: re.sub(r"\s+", " ", cells[i].get_text(" ", strip=True)).strip()
               for k, i in idx.items() if i is not None}
        if not row.get("university") or not row.get("date"):
            continue

        available = "AVAILABLE SEATS" in row["state"].upper()
        seat_text = row["seats"].replace(".", "").replace(",", "")
        match = re.search(r"\d+", seat_text)
        seats = int(match.group()) if match and available else 0

        # Stable identity for a specific exam sitting.
        key = "|".join([
            row["format"].upper(), row["university"].upper(),
            row["city"].upper(), row["date"], row["deadline"]
        ])
        results[key] = {
            "format": row["format"],
            "university": row["university"],
            "city": row["city"],
            "deadline": row["deadline"],
            "date": row["date"],
            "available": available,
            "seats": seats,
        }
    if not results:
        raise RuntimeError("CISIA page loaded, but no calendar rows were parsed.")
    return results


def read_previous():
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise RuntimeError("state.json exists but cannot be read; refusing to overwrite history.")


def row_text(r):
    return (
        f"{r['format']} | {r['university']}\n"
        f"City: {r['city']}\nExam date: {r['date']}\n"
        f"Booking deadline: {r['deadline']}\nSeats shown: {r['seats']}\n"
        f"Calendar: {URL}"
    )


def main():
    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID GitHub secret.")

    current = fetch_calendar()
    previous = read_previous()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if previous is None:
        available = [r for r in current.values() if r["available"]]
        if available:
            msg = "CEnT-S MONITOR STARTED\nCurrent available sessions:\n\n"
            msg += "\n\n--------------------\n\n".join(row_text(r) for r in available)
        else:
            msg = f"CEnT-S monitor started. No available seats found on first check.\n{URL}"
        telegram_send(msg)
        print(f"Initial baseline saved; {len(available)} available session(s).")
    else:
        alerts = []
        for key, row in current.items():
            old = previous.get(key)
            if row["available"] and (old is None or not old.get("available", False)):
                alerts.append("NEWLY AVAILABLE SESSION\n\n" + row_text(row))
            elif row["available"] and old and row["seats"] > int(old.get("seats", 0)):
                alerts.append(
                    "SEAT COUNT INCREASED\n\n" + row_text(row)
                    + f"\nPreviously: {old.get('seats', 0)}"
                )

        if alerts:
            telegram_send("CEnT-S SEAT ALERT\n\n" + "\n\n--------------------\n\n".join(alerts))
            print(f"Sent {len(alerts)} seat alert(s).")
        else:
            print("No new availability or seat increases.")

    snapshot = {
        "checked_at_utc": now,
        "sessions": current,
    }
    STATE_PATH.write_text(json.dumps(snapshot["sessions"], indent=2, ensure_ascii=False),
                          encoding="utf-8")
    print(f"Saved {len(current)} sessions to state.json at {now}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"MONITOR ERROR: {exc}", file=sys.stderr)
        raise
