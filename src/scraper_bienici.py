"""
Scraper Bienici (Playwright) - VERIFIE le 02/08/2026 par test reel en navigateur
(Claude in Chrome, session de developpement).

Remplace la version precedente basee sur l'endpoint realEstateAds.json : ce
endpoint repond HTTP 200 mais ignore silencieusement tous les filtres testes
(postalCode, propertyType, onTheMarket, zoneIdsByTypes avec code INSEE,
keywords) - deux requetes avec des filtres differents ont renvoye un resultat
strictement identique, sans rapport avec Bordeaux. Non exploitable.

Cette version pilote un navigateur headless sur la vraie page de recherche.
Selecteurs CSS confirmes par inspection reelle du DOM le 02/08/2026 :
  - conteneur annonce : article.ad-overview
  - titre (contient pieces/surface/code postal) : .ad-overview-details__title
  - prix : .ad-price
  - agence : .account-logo__display-name
  - lien : premier a[href] de la carte

Limites connues (non resolues a ce stade) :
  - Le DPE n'apparait pas dans la vue liste, seulement sur la fiche detail de
    chaque annonce. Non recupere ici (ajouterait une requete par annonce,
    donc plus de temps + plus de risque de detection). A faire si besoin.
  - is_individual reste force a False : aucun badge "particulier" identifie
    de facon fiable sur la carte pendant ce test. A verifier sur un
    echantillon plus large avant de faire confiance a l'exclusion agences.
  - Le filtre natif "Meuble" existe dans l'UI bienici mais son parametre
    d'URL exact n'a pas ete identifie. Le scan de mots-cles (filters.py)
    reste donc la seule detection active pour l'instant.
  - Selecteurs CSS susceptibles de changer sans preavis (site en evolution
    continue) : revalider si le scraper renvoie 0 resultat du jour au
    lendemain.
"""
import re

from .filters import is_furnished, matches_criteria

SEARCH_URL_TEMPLATE = (
    "https://www.bienici.com/recherche/achat/bordeaux-gare-saint-jean-33000-gare-saint-jean"
    "/appartement/{rooms}-pieces?mode=liste"
)

TITLE_RE = re.compile(r"(?P<rooms>\d+)\s*pi[eè]ces?\s*(?P<surface>[\d,.]+)\s*m2?\s*(?P<postal>\d{5})")
PRICE_RE = re.compile(r"([\d\s ]+)\s*€")


def _parse_card(card_text, title_text, price_text, agency_text, href):
    normalized_title = (title_text or "").replace("²", "2").replace("²", "2")
    m = TITLE_RE.search(normalized_title)
    rooms = int(m.group("rooms")) if m else None
    surface = float(m.group("surface").replace(",", ".")) if m else None
    postal = m.group("postal") if m else None

    price_clean = (price_text or "").replace(" ", " ")
    price_match = PRICE_RE.search(price_clean)
    price = int(price_match.group(1).replace(" ", "")) if price_match else None

    return {
        "id": href,
        "title": (title_text or "").strip(),
        "description": (card_text or "")[:1000],
        "price": price,
        "surface": surface,
        "price_per_m2": round(price / surface) if price and surface else None,
        "room_count": rooms,
        "postal_code": postal,
        "dpe": None,  # non disponible en vue liste, cf. limites ci-dessus
        "url": f"https://www.bienici.com{href}" if href and href.startswith("/") else href,
        "agency": (agency_text or "Inconnu").strip(),
        "is_individual": False,  # non verifie, cf. limites ci-dessus
        "source": "bienici",
    }


def fetch_bienici_listings(config, session=None):
    """
    `session` (ScraperSession HTTP) n'est pas utilise ici : conserve pour
    compatibilite de signature avec main.py. Playwright gere son propre
    navigateur et ses propres en-tetes.
    Necessite : pip install playwright && playwright install chromium
    """
    from playwright.sync_api import sync_playwright  # import tardif : dependance optionnelle

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="fr-FR")
        try:
            for rooms in config["search"]["room_counts"]:
                url = SEARCH_URL_TEMPLATE.format(rooms=rooms)
                page.goto(url, wait_until="networkidle", timeout=30000)
                try:
                    page.wait_for_selector("article.ad-overview", timeout=15000)
                except Exception:
                    print(f"[bienici] Aucune annonce trouvee pour {rooms} pieces (selecteur absent).")
                    continue

                cards = page.query_selector_all("article.ad-overview")
                for card in cards:
                    title_el = card.query_selector(".ad-overview-details__title")
                    price_el = card.query_selector(".ad-price")
                    agency_el = card.query_selector(".account-logo__display-name")
                    link_el = card.query_selector("a[href]")

                    listing = _parse_card(
                        card_text=card.inner_text(),
                        title_text=title_el.inner_text() if title_el else "",
                        price_text=price_el.inner_text() if price_el else "",
                        agency_text=agency_el.inner_text() if agency_el else "",
                        href=link_el.get_attribute("href") if link_el else None,
                    )
                    if matches_criteria(listing, config):
                        listing["furnished"] = is_furnished(listing, config)
                        results.append(listing)
        finally:
            browser.close()
    return results
