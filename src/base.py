"""
Session HTTP mutualisée : rotation de User-Agent, délais aléatoires,
support proxy optionnel. Utilisée par tous les scrapers de sources.
"""
import random
import time
import requests


class ScraperSession:
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.user_agents = self._load_lines(config["request"]["user_agents_file"]) or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        ]
        self.proxies = (
            self._load_lines(config["request"]["proxies"]["list_file"])
            if config["request"]["proxies"]["enabled"]
            else []
        )

    @staticmethod
    def _load_lines(path):
        try:
            with open(path, encoding="utf-8") as f:
                return [l.strip() for l in f if l.strip()]
        except FileNotFoundError:
            return []

    def _headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }

    def _proxy_dict(self):
        if not self.proxies:
            return None
        p = random.choice(self.proxies)
        return {"http": p, "https": p}

    def get(self, url, params=None):
        delay = random.uniform(
            self.config["request"]["min_delay_seconds"],
            self.config["request"]["max_delay_seconds"],
        )
        time.sleep(delay)
        return self.session.get(
            url,
            params=params,
            headers=self._headers(),
            proxies=self._proxy_dict(),
            timeout=20,
        )
