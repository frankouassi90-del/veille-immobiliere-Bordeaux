"""
Scraper SeLoger — DÉSACTIVÉ PAR DÉFAUT (sources.seloger.enabled: false).

SeLoger est protégé par Datadome (anti-bot avancé). Un scraping fiable
nécessite en pratique un navigateur headless (ex. Playwright) avec gestion
de fingerprint + proxies résidentiels rotatifs. Un simple requests/BeautifulSoup
comme ci-dessous fonctionnera de façon intermittente au mieux, et peut être
bloqué (429/403) après quelques requêtes.
Incertain : taux de succès réel non testé dans cette session (pas d'accès
réseau sortant vers seloger.com ici). Les sélecteurs CSS ci-dessous sont
indicatifs et doivent être revalidés sur le DOM réel avant usage.

Rappel légal : le scraping automatisé de SeLoger est généralement interdit
par ses conditions d'utilisation (CGU). À vos risques (blocage IP a minima).
"""
from bs4 import BeautifulSoup

from .filters import is_furnished, matches_criteria

SEARCH_URL = (
    "https://www.seloger.com/immobilier/achat/immo-bordeaux-33/"
    "quartier-saint-jean-belcier-carle-vernet-albert-1er/bien-appartement/"
)


def fetch_seloger_listings(config, session):
    if not config["sources"]["seloger"]["enabled"]:
        return []

    resp = session.get(SEARCH_URL)
    if resp.status_code != 200:
        print(f"[SeLoger] Blocage probable (status {resp.status_code}), source ignorée ce run.")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    # Sélecteurs à valider : la structure DOM de SeLoger change fréquemment.
    for card in soup.select("[data-testid='serp-core-classified-card-testid']"):
        title_el = card.select_one("h2, [class*='title']")
        link_el = card.select_one("a[href]")
        listing = {
            "id": link_el["href"] if link_el else None,
            "title": title_el.get_text(strip=True) if title_el else "",
            "description": "",
            "price": None,
            "surface": None,
            "price_per_m2": None,
            "room_count": None,
            "postal_code": "33800",
            "dpe": None,
            "url": link_el["href"] if link_el else "",
            "agency": "Inconnu",
            "is_individual": False,
            "source": "seloger",
        }
        if matches_criteria(listing, config):
            listing["furnished"] = is_furnished(listing, config)
            results.append(listing)
    return results
