# Veille immobilière — T2/T3/T4 Belcier, Bordeaux (33800)

Scraper + système d'alerte pour surveiller quotidiennement les annonces
d'agences (particuliers exclus) sur Belcier / Carle Vernet / Gare Saint-Jean
/ Nansouty, avec détection best-effort du critère "meublé".

## Ce qui est fait

- `config.yaml` : tous les critères (zone, typologie, agences uniquement, meublé) et réglages.
- `src/scraper_bienici.py` : source principale, via l'API JSON semi-publique de bienici.com.
- `src/scraper_seloger.py` : source secondaire, **désactivée par défaut** (voir limite ci-dessous).
- `src/filters.py` : application des critères + détection "meublé" par mots-clés dans le texte de l'annonce (aucun portail n'a de filtre natif meublé pour la vente).
- `src/storage.py` : sauvegarde JSON (`data/listings.json`) + export optionnel Google Sheets + détection des nouvelles annonces (diff vs run précédent).
- `src/alerts.py` : alerte email (SMTP) et/ou webhook (Slack/Discord/n8n...) sur les nouveautés uniquement.
- `main.py` : orchestrateur, à exécuter à chaque run.
- `.github/workflows/daily-scan.yml` : exécution automatique quotidienne via GitHub Actions (gratuit), avec commit du fichier de données et alerte.

## Ce qui n'est PAS vérifié (honnêteté avant mise en prod)

- **Aucun test réseau réel effectué dans cette session** : pas d'accès sortant vers bienici.com/seloger.com depuis cet environnement. Les noms de champs JSON de bienici (`surfaceArea`, `roomsQuantity`, `energyClassification`...) viennent de la structure connue publiquement, pas d'un appel vérifié aujourd'hui. **Premier lancement recommandé en local avec un `print(response.json())` avant de faire confiance au résultat.**
- **SeLoger est protégé par Datadome** (anti-bot avancé). Le scraper fourni (`requests` + BeautifulSoup) fonctionnera de façon intermittente au mieux, voire pas du tout. Pour une fiabilité correcte il faudrait Playwright headless + proxies résidentiels rotatifs, un investissement technique et financier supplémentaire non inclus ici.
- **CGU** : le scraping automatisé de portails comme SeLoger est généralement interdit par leurs conditions d'utilisation. Bienici est historiquement plus tolérant (API ouverte utilisée par de nombreux projets tiers) mais rien ne garantit que ça reste le cas. Risque principal : blocage IP, pas de risque pénal identifié pour un usage personnel non commercial, mais **non vérifié juridiquement**.
- **Critère "meublé"** : détection par mots-clés dans le texte de l'annonce uniquement. Si l'agence ne mentionne pas explicitement "meublé"/"LMNP", le bien ne sera pas identifié comme tel même s'il l'est (faux négatifs probables).

## Installation

```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
python main.py
```

## Activer les alertes

1. Email : passer `alerts.email.enabled` à `true` dans `config.yaml`, renseigner `smtp_host`/`from_addr`, et définir la variable d'environnement `SMTP_PASSWORD`.
2. Webhook (Slack/Discord/n8n) : passer `alerts.webhook.enabled` à `true`, définir la variable d'environnement `WEBHOOK_URL`.

## Automatisation quotidienne (recommandé : GitHub Actions)

1. Pousser ce dossier dans un repo GitHub (privé de préférence, les données immobilières n'ont rien de sensible mais autant rester discret).
2. Dans les Settings > Secrets du repo, ajouter `SMTP_PASSWORD` et/ou `WEBHOOK_URL`.
3. Le workflow `.github/workflows/daily-scan.yml` tourne tous les jours à 07h00 UTC, sans serveur à maintenir.

Alternative : cron classique sur ta machine ou un petit VPS (`0 7 * * * cd /path/veille-immo-belcier && python main.py`).

## Prochaine étape suggérée

Trouver l'ID de zone bienici pour Belcier/33800 (à récupérer dans l'onglet réseau du navigateur en filtrant une recherche manuelle sur bienici.com) et le renseigner dans `zoneIdsByTypes.zoneIds` de `src/scraper_bienici.py`, puis lancer un premier run test en local avant d'automatiser.

## Journal de vérification — 02/08/2026 (session de test réel)

Test effectué en conditions réelles (accès réseau direct + navigateur Chrome connecté) pour valider les hypothèses du scraper avant mise en prod.

**Confirmé :**
- L'endpoint `https://www.bienici.com/realEstateAds.json?filters=...` répond (HTTP 200) mais **ignore silencieusement tous les paramètres de filtre testés** (`postalCode`, `propertyType`, `onTheMarket`, `zoneIdsByTypes` avec code INSEE, `keywords`) : deux requêtes avec des filtres différents ont renvoyé un résultat strictement identique (5 annonces hors-marché, sans rapport avec Bordeaux). **Cet endpoint n'est pas exploitable pour le scraping**, contrairement à ce que prévoyait `src/scraper_bienici.py` initial. La recherche réelle du site passe très probablement par un canal WebSocket (`watcher.bienici.com/socket.io`), pas par une simple requête REST.
- L'URL humaine `https://www.bienici.com/recherche/achat/bordeaux-33000-gare-saint-jean/appartement/{N}-pieces?mode=liste` fonctionne et affiche les vraies annonces (51 T2 trouvés au moment du test), avec la carte centrée exactement sur Belcier/Carle Vernet/Nansouty. `{N}` = nombre de pièces (2, 3, 4). Le paramètre `?mode=liste` force la vue liste (plus simple à parser qu'une carte).
- **Correction d'une erreur précédente** : bienici propose bien un filtre natif **"Meublé" / "Non meublé"** en achat (section "Vos exigences particulières" des critères avancés). L'affirmation antérieure comme quoi "aucun portail n'a de filtre meublé pour la vente" était fausse. Le paramètre d'URL exact qui active ce filtre n'a pas encore été identifié (nécessite de cocher la case dans le navigateur et de lire l'URL résultante).
- Deux annonces T2 réelles capturées et recoupées avec la recherche SeLoger précédente : HORIA / LEGENDRE IMMOBILIER, 235 000 €, 49 m², "cœur du quartier Belcier — Saint-Jean" (identique sur les deux portails, bon signe de fiabilité) ; et une deuxième via iad France, rue Carle Vernet, 47 m², 210 000 €, résidence 2021, à quelques mètres de l'arrêt de tram Belcier.

**Conséquence pour le code :** `src/scraper_bienici.py` doit être réécrit pour piloter un navigateur headless (Playwright) sur l'URL `?mode=liste` ci-dessus plutôt que d'appeler l'endpoint JSON. C'est la prochaine tâche technique concrète, pas encore faite dans ce dossier.

## Mise à jour — scraper Bienici réécrit en Playwright (02/08/2026)

`src/scraper_bienici.py` a été entièrement réécrit : il pilote maintenant un navigateur headless (Playwright) sur `https://www.bienici.com/recherche/achat/bordeaux-gare-saint-jean-33000-gare-saint-jean/appartement/{2,3,4}-pieces?mode=liste` au lieu d'appeler l'endpoint JSON cassé.

**Vérifié réellement (via Claude in Chrome, pas une supposition) :**
- Sélecteurs CSS confirmés en inspectant le DOM en direct : `article.ad-overview` (carte annonce), `.ad-overview-details__title` (titre avec pièces/surface/code postal), `.ad-price` (prix), `.account-logo__display-name` (agence).
- Deux vraies annonces extraites pendant le test : Citya Immobilier Atlantis, T2 46 m², 120 000 € (bien loué, profil investisseur), et HORIA/Legendre Immobilier déjà vu sur SeLoger (235 000 €, 49 m²).

**Non vérifié / limite assumée :**
- Je n'ai pas pu exécuter un run Playwright complet de bout en bout dans ce bac à sable (le téléchargement de Chromium fait ~184 Mo et dépasse la limite de temps par commande de cet environnement, ~45 s). Le code est syntaxiquement valide (`py_compile` passé) et basé sur des sélecteurs vérifiés en direct, mais **le premier run réel reste à faire sur ta machine** :
  ```
  pip install -r requirements.txt
  playwright install chromium
  python main.py
  ```
- `is_individual` reste forcé à `False` (aucun badge "particulier" identifié de façon fiable sur les cartes pendant ce test) : le filtre "agences uniquement" n'est donc pas encore garanti à 100%. À vérifier sur un échantillon plus large.
- DPE non récupéré (absent de la vue liste, uniquement sur la fiche détail — ajouter une requête par annonce si ce champ est indispensable).
