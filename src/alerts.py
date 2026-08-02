"""Alertes email (SMTP) et webhook (Slack/Discord/n8n...) sur nouvelles annonces."""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


def _format_listing(l):
    if l.get("furnished") is True:
        meuble = "Meublé (détecté)"
    elif l.get("furnished") is False:
        meuble = "Non renseigné meublé"
    else:
        meuble = "Critère meublé désactivé"
    return (
        f"- {l.get('title')}\n"
        f"  Prix: {l.get('price')} EUR | Surface: {l.get('surface')} m2 | "
        f"Prix/m2: {l.get('price_per_m2')} | Pieces: {l.get('room_count')} | "
        f"DPE: {l.get('dpe')} | {meuble}\n"
        f"  Agence: {l.get('agency')}\n"
        f"  Lien: {l.get('url')}\n"
    )


def send_email_alert(new_listings, config):
    conf = config["alerts"]["email"]
    if not conf["enabled"] or not new_listings:
        return
    password = os.environ.get(conf["smtp_password_env"], "")

    body = "Nouvelles annonces T2/T3/T4 - Belcier Bordeaux\n\n"
    body += "\n".join(_format_listing(l) for l in new_listings)

    msg = MIMEMultipart()
    msg["Subject"] = f"[Veille immo Belcier] {len(new_listings)} nouvelle(s) annonce(s)"
    msg["From"] = conf["from_addr"]
    msg["To"] = conf["to_addr"]
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(conf["smtp_host"], conf["smtp_port"]) as server:
        server.starttls()
        server.login(conf["from_addr"], password)
        server.sendmail(conf["from_addr"], conf["to_addr"], msg.as_string())


def send_webhook_alert(new_listings, config):
    conf = config["alerts"]["webhook"]
    if not conf["enabled"] or not new_listings:
        return
    url = os.environ.get(conf["url_env"], "")
    if not url:
        print("Webhook activé mais URL absente (variable d'environnement manquante).")
        return
    text = f"{len(new_listings)} nouvelle(s) annonce(s) T2/T3/T4 - Belcier Bordeaux\n\n"
    text += "\n".join(_format_listing(l) for l in new_listings)
    requests.post(url, json={"text": text}, timeout=10)
