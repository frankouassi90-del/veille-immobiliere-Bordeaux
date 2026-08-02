"""Application des critères de recherche définis dans config.yaml."""


def matches_criteria(listing, config):
    s = config["search"]
    if listing.get("postal_code") not in s["postal_codes"]:
        return False
    if listing.get("room_count") not in s["room_counts"]:
        return False
    if s["seller_type"] == "agency_only" and listing.get("is_individual", False):
        return False
    return True


def is_furnished(listing, config):
    """
    Retourne True/False si le mot-clé "meublé"/"LMNP" apparaît dans le
    titre ou la description, None si le critère est désactivé.
    Aucun portail n'expose de filtre natif "meublé" pour la vente : ceci
    reste une détection texte, donc approximative (faux négatifs probables
    si l'agence ne précise pas ce point dans l'annonce).
    """
    if not config["search"]["furnished"]["enabled"]:
        return None
    text = f"{listing.get('title', '')} {listing.get('description', '')}".lower()
    keywords = config["search"]["furnished"]["keywords"]
    return any(k.lower() in text for k in keywords)
