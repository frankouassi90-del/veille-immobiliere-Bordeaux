"""Orchestrateur : lance les scrapers activés, calcule le diff, alerte."""
import yaml

from src.alerts import send_email_alert, send_webhook_alert
from src.base import ScraperSession
from src.scraper_bienici import fetch_bienici_listings
from src.scraper_seloger import fetch_seloger_listings
from src.storage import diff_new_listings, export_to_google_sheets, load_previous, save_current


def load_config(path="config.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    session = ScraperSession(config)

    all_listings = []
    if config["sources"]["bienici"]["enabled"]:
        all_listings += fetch_bienici_listings(config, session)
    if config["sources"]["seloger"]["enabled"]:
        all_listings += fetch_seloger_listings(config, session)

    json_path = config["storage"]["json_path"]
    previous = load_previous(json_path)
    new_listings = diff_new_listings(previous, all_listings)

    save_current(json_path, all_listings)
    export_to_google_sheets(all_listings, config)

    send_email_alert(new_listings, config)
    send_webhook_alert(new_listings, config)

    print(f"{len(all_listings)} annonces au total, {len(new_listings)} nouvelle(s) ce run.")


if __name__ == "__main__":
    main()
