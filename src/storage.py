"""Persistance JSON + export optionnel Google Sheets + détection des nouveautés."""
import json
import os


def load_previous(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    return {(item.get("id") or item.get("url")): item for item in items}


def save_current(path, listings):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)


def diff_new_listings(previous, current):
    return [l for l in current if (l.get("id") or l.get("url")) not in previous]


def export_to_google_sheets(listings, config):
    conf = config["storage"]["google_sheets"]
    if not conf["enabled"]:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("gspread/google-auth non installés : pip install gspread google-auth")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(conf["service_account_file"], scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(conf["spreadsheet_id"])
    ws = sh.sheet1
    ws.clear()
    if not listings:
        return
    headers = list(listings[0].keys())
    ws.append_row(headers)
    for l in listings:
        ws.append_row([str(l.get(h, "")) for h in headers])
