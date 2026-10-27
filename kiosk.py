"""Bestelzuil voor de eindgebruiker (vensterbreed, touch-vriendelijk).

Wordt door dashboard.py geserveerd op http://localhost:8080/ ; de technische
bedieningsinterface staat op /technisch. Beide schermen hebben een knop om naar
de andere te wisselen.

Het assortiment en de voorraad staan voorlopig vast in DRINKS hieronder. Een
geplaatste bestelling wordt gecontroleerd en krijgt een bestelnummer, maar gaat
nog niet naar de robot en verlaagt de voorraad niet (zie place_order).

Productfoto's staan in static/drinks/<id>.jpg (of .png/.webp); zonder foto toont
de zuil een getekend blikje of flesje. Bronvermelding: static/drinks/CREDITS.md.
"""

import os
import threading

CATEGORIES = [
  ("frisdrank", "Frisdrank"),
  ("icetea", "Ice tea"),
  ("energy", "Energy"),
  ("water", "Water"),
  ("bier", "Bier"),
  ("seltzer", "Hard seltzer"),
  ("overig", "Overig"),
]

# Maximaal aantal van eenzelfde drankje per bestelling.
MAX_PER_DRINK = 10


def _drink(id, name, label, category, container, volume_ml, price_cents, color, accent, ink, stock, abv=0.0):
  return {
    "id": id, "name": name, "label": label, "category": category,
    "container": container, "volume_ml": volume_ml, "price_cents": price_cents,
    "color": color, "accent": accent, "ink": ink, "stock": stock, "abv": abv,
  }


# color = kleur van blik/fles, accent = band (blik) of dop en etiket (fles),
# ink = tekst op de band. stock = aantal op voorraad, 0 = niet beschikbaar.
# abv = alcoholpercentage; vanaf 0.5% vraagt de zuil of de klant 18+ is.
DRINKS = [
  _drink("cola", "Coca-Cola", "COLA", "frisdrank", "blik", 330, 260, "#e41e2b", "#ffffff", "#e41e2b", 8),
  _drink("cola-zero", "Coca-Cola Zero", "ZERO", "frisdrank", "blik", 330, 260, "#141414", "#e41e2b", "#ffffff", 6),
  _drink("pepsi-max", "Pepsi Max", "PEPSI", "frisdrank", "blik", 330, 250, "#0b1f4b", "#2563c9", "#ffffff", 5),
  _drink("fanta", "Fanta Orange", "FANTA", "frisdrank", "blik", 330, 250, "#f7821b", "#1d5fb3", "#ffffff", 4),
  _drink("fanta-cassis", "Fanta Cassis", "CASSIS", "frisdrank", "blik", 330, 250, "#6b2c7a", "#f2c94c", "#6b2c7a", 2),
  _drink("sprite", "Sprite", "SPRITE", "frisdrank", "blik", 330, 250, "#0a8a3e", "#f2d21a", "#0a5a2a", 7),
  _drink("7up", "7UP", "7UP", "frisdrank", "blik", 330, 250, "#1aa64a", "#ffffff", "#e3262d", 3),
  _drink("dr-pepper", "Dr Pepper", "DR PEPPER", "frisdrank", "blik", 330, 260, "#6d1a24", "#ffffff", "#6d1a24", 0),
  _drink("lipton-sparkling", "Lipton Ice Tea Sparkling", "ICE TEA", "icetea", "blik", 330, 250, "#f4c21b", "#d0261f", "#ffffff", 6),
  _drink("lipton-green", "Lipton Ice Tea Green", "GREEN", "icetea", "blik", 330, 250, "#7cbf3c", "#f4e04d", "#2f5d1a", 5),
  _drink("fuze-peach", "Fuze Tea Perzik", "FUZE", "icetea", "blik", 330, 250, "#f29a7b", "#2d6b3a", "#ffffff", 0),
  _drink("red-bull", "Red Bull", "RED BULL", "energy", "blik", 250, 275, "#1d3d8f", "#d7dbe2", "#c8102e", 6),
  _drink("red-bull-sf", "Red Bull Sugarfree", "SUGARFREE", "energy", "blik", 250, 275, "#9cc3e6", "#1d3d8f", "#ffffff", 2),
  _drink("monster", "Monster Energy", "MONSTER", "energy", "blik", 500, 325, "#141414", "#7ad420", "#141414", 0),
  _drink("spa-reine", "Spa Reine", "SPA", "water", "fles", 500, 200, "#8fc6ea", "#1d5fa8", "#1d5fa8", 9),
  _drink("spa-intense", "Spa Intense bruisend", "SPA", "water", "fles", 500, 200, "#8fc6ea", "#d0261f", "#d0261f", 4),
  _drink("chaudfontaine", "Chaudfontaine Still", "CHAUD.", "water", "fles", 500, 200, "#a9d2ee", "#1f4f9c", "#1f4f9c", 3),
  _drink("chocomel", "Chocomel", "CHOCOMEL", "overig", "blik", 250, 225, "#f5c400", "#5a3418", "#f5c400", 4),
  _drink("bitter-lemon", "Royal Club Bitter Lemon", "BITTER", "overig", "blik", 330, 250, "#f2e35a", "#1a4f2a", "#ffffff", 3),
  _drink("heineken", "Heineken", "HEINEKEN", "bier", "blik", 330, 275, "#126b38", "#ffffff", "#126b38", 8, abv=5.0),
  _drink("amstel", "Amstel", "AMSTEL", "bier", "blik", 330, 265, "#c8102e", "#ffffff", "#c8102e", 6, abv=5.0),
  _drink("grolsch", "Grolsch Premium Pilsner", "GROLSCH", "bier", "blik", 330, 275, "#1f6b3a", "#f0e6c8", "#1f6b3a", 5, abv=5.0),
  _drink("hertog-jan", "Hertog Jan Pilsener", "HERTOG JAN", "bier", "blik", 330, 285, "#6b4a1f", "#e8c66a", "#3a2410", 3, abv=5.1),
  _drink("bavaria", "Bavaria Premium Pilsner", "BAVARIA", "bier", "blik", 330, 250, "#1b4a9c", "#ffffff", "#1b4a9c", 0, abv=5.0),
  _drink("heineken-00", "Heineken 0.0", "0.0", "bier", "blik", 330, 275, "#0f6a3a", "#1f4fa8", "#ffffff", 5),
  _drink("stelz-apple", "St\u00eblz Hard Seltzer Apple", "ST\u00cbLZ", "seltzer", "blik", 250, 325, "#f4f3ef", "#6cb33f", "#ffffff", 6, abv=4.5),
  _drink("stelz-strawberry", "St\u00eblz Hard Lemonade Strawberry", "ST\u00cbLZ", "seltzer", "blik", 250, 325, "#f4f3ef", "#e0344f", "#ffffff", 4, abv=4.5),
]

_DRINKS_BY_ID = {drink["id"]: drink for drink in DRINKS}

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "drinks")
IMAGE_TYPES = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

_order_lock = threading.Lock()
_next_order_number = 1


class OrderError(ValueError):
  """Bestelling klopt niet; de tekst is bedoeld voor de eindgebruiker."""


def _image_file(drink_id):
  for ext in IMAGE_TYPES:
    name = drink_id + ext
    if os.path.isfile(os.path.join(IMAGE_DIR, name)):
      return name
  return None


def menu():
  drinks = []
  for drink in DRINKS:
    image = _image_file(drink["id"])
    drinks.append(dict(drink, image=f"/static/drinks/{image}" if image else None))
  return {
    "categories": [{"id": key, "name": name} for key, name in CATEGORIES],
    "drinks": drinks,
    "max_per_drink": MAX_PER_DRINK,
  }


def drink_image(name):
  """(bytes, content-type) voor /static/drinks/<name>, of None. Alleen foto's van bekende drankjes."""
  drink_id, ext = os.path.splitext(name)
  if drink_id not in _DRINKS_BY_ID or ext not in IMAGE_TYPES:
    return None
  try:
    with open(os.path.join(IMAGE_DIR, name), "rb") as f:
      return f.read(), IMAGE_TYPES[ext]
  except OSError:
    return None


def place_order(items):
  """Controleert een bestelling ([{"id": ..., "qty": ...}]) en geeft het bestelnummer.

  Stuurt nog niets naar de robot en verlaagt de voorraad niet.
  """
  global _next_order_number
  if not isinstance(items, list) or not items:
    raise OrderError("Je winkelmandje is leeg.")
  wanted = {}
  for item in items:
    if not isinstance(item, dict):
      raise OrderError("Ongeldige bestelling.")
    drink = _DRINKS_BY_ID.get(item.get("id"))
    qty = item.get("qty")
    if drink is None or not isinstance(qty, int) or isinstance(qty, bool) or qty < 1:
      raise OrderError("Ongeldige bestelling.")
    wanted[drink["id"]] = wanted.get(drink["id"], 0) + qty
  short = [
    _DRINKS_BY_ID[drink_id]["name"]
    for drink_id, qty in wanted.items()
    if qty > min(_DRINKS_BY_ID[drink_id]["stock"], MAX_PER_DRINK)
  ]
  if short:
    raise OrderError("Niet (meer) genoeg beschikbaar: " + ", ".join(short) + ".")
  with _order_lock:
    number = _next_order_number
    _next_order_number = number % 999 + 1
  return {
    "order_number": number,
    "items": [{"id": drink_id, "name": _DRINKS_BY_ID[drink_id]["name"], "qty": qty} for drink_id, qty in wanted.items()],
  }


KIOSK_PAGE = r"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Drankautomaat bestellen</title>
<style>
  :root {
    --page: #f7f4ee;
    --surface: #ffffff;
    --surface-2: #f0ebe2;
    --ink: #1c1a16;
    --ink-2: #5a554c;
    --muted: #8c867b;
    --border: rgba(28,26,22,0.10);
    --primary: #d9480f;
    --primary-press: #b83a0a;
    --primary-ink: #ffffff;
    --primary-soft: #fde8dc;
    --good: #12805c;
    --warn: #b45309;
    --out: #8c867b;
    --danger: #c92a2a;
    --shadow: 0 1px 2px rgba(28,26,22,0.06), 0 8px 24px rgba(28,26,22,0.07);
    --radius: 22px;
  }
  * { box-sizing: border-box; }
  html { font-size: clamp(14px, 0.9vmin + 8px, 21px); }
  html, body { height: 100%; margin: 0; }
  body {
    background: var(--page); color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-tap-highlight-color: transparent; -webkit-user-select: none; user-select: none;
    overscroll-behavior: none; touch-action: manipulation; overflow: hidden;
  }
  [hidden] { display: none !important; }
  button { font: inherit; color: inherit; }
  a { color: inherit; }
  .num { font-variant-numeric: tabular-nums; }
  .screen { position: fixed; inset: 0; display: flex; flex-direction: column; min-height: 0; }

  /* -- knoppen -- */
  .btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 0.6rem;
    min-height: 3.6rem; padding: 0 1.6rem; border-radius: 999px; border: 0; cursor: pointer;
    font-size: 1.1rem; font-weight: 700; white-space: nowrap; text-decoration: none;
    transition: transform 0.08s ease, background-color 0.15s ease;
  }
  .btn:active:not(:disabled) { transform: scale(0.97); }
  .btn:disabled { cursor: default; opacity: 0.4; }
  .btn-primary { background: var(--primary); color: var(--primary-ink); }
  .btn-primary:active:not(:disabled) { background: var(--primary-press); }
  .btn-secondary { background: var(--surface); color: var(--ink); box-shadow: inset 0 0 0 2px var(--border); }
  .btn-lg { min-height: 4.2rem; padding: 0 2.2rem; font-size: 1.25rem; }
  .btn svg { width: 1.3em; height: 1.3em; flex: none; }
  .icon-btn {
    display: inline-grid; place-items: center; width: 3rem; height: 3rem; border-radius: 50%;
    border: 0; background: transparent; color: var(--muted); cursor: pointer; text-decoration: none;
  }
  .icon-btn svg { width: 1.4rem; height: 1.4rem; }
  .ghost-btn {
    display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.6rem 1rem; border-radius: 999px;
    border: 0; background: rgba(255,255,255,0.55); color: var(--ink-2); cursor: pointer;
    font-size: 0.85rem; font-weight: 600; text-decoration: none;
  }
  .ghost-btn svg { width: 1.1rem; height: 1.1rem; }

  /* -- startscherm -- */
  .welcome { background: radial-gradient(120% 90% at 50% 0%, #fff3e6 0%, var(--page) 60%); }
  .welcome-hit {
    flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 1.2rem; padding: 2rem; text-align: center; cursor: pointer; outline: none;
  }
  .welcome-cans { display: flex; align-items: flex-end; justify-content: center; gap: 0.8rem; margin-bottom: 1.5rem; }
  .welcome-cans .drink-art { height: 10rem; width: auto; filter: drop-shadow(0 10px 14px rgba(28,26,22,0.18)); }
  .welcome-cans img.drink-art { filter: none; }
  .welcome-cans .drink-art:nth-child(odd) { transform: translateY(-0.8rem) rotate(-4deg); }
  .welcome-cans .drink-art:nth-child(even) { transform: rotate(4deg); }
  .welcome-title { font-size: 4.2rem; line-height: 1.05; margin: 0; font-weight: 800; letter-spacing: -0.02em; }
  .welcome-sub { font-size: 1.5rem; margin: 0; color: var(--ink-2); }
  .welcome-cta {
    margin-top: 2rem; display: inline-flex; align-items: center; gap: 0.8rem;
    padding: 1.4rem 3rem; border-radius: 999px; background: var(--primary); color: var(--primary-ink);
    font-size: 1.6rem; font-weight: 800; box-shadow: 0 10px 30px color-mix(in srgb, var(--primary) 35%, transparent);
    animation: pulse 2.2s ease-in-out infinite;
  }
  .welcome-cta svg { width: 1.8rem; height: 1.8rem; }
  @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
  .welcome-corner {
    position: absolute; left: 0; right: 0; bottom: 0; display: flex; justify-content: space-between;
    padding: 1rem calc(1rem + env(safe-area-inset-right)) calc(1rem + env(safe-area-inset-bottom)) calc(1rem + env(safe-area-inset-left));
    pointer-events: none;
  }
  .welcome-corner > * { pointer-events: auto; }
  .credits { align-self: center; font-size: 0.7rem; color: var(--muted); }

  /* -- kop van menu en winkelmandje -- */
  .head {
    display: flex; align-items: center; gap: 1.2rem; padding: 1.1rem 1.6rem;
    background: var(--surface); border-bottom: 1px solid var(--border);
  }
  .head h1 { margin: 0; font-size: 1.7rem; font-weight: 800; letter-spacing: -0.01em; }
  .head p { margin: 0.15rem 0 0; color: var(--ink-2); font-size: 1rem; }
  .head-grow { flex: 1; min-width: 0; }
  .legend { display: flex; gap: 1.2rem; flex-wrap: wrap; font-size: 0.9rem; color: var(--ink-2); }
  .legend span { display: inline-flex; align-items: center; gap: 0.45rem; }
  .sdot { width: 0.7rem; height: 0.7rem; border-radius: 50%; flex: none; background: var(--good); }
  .sdot.low { background: var(--warn); }
  .sdot.out { background: transparent; box-shadow: inset 0 0 0 2px var(--out); }
  .offline {
    padding: 0.8rem 1.6rem; background: #fff1f0; color: var(--danger); font-weight: 600; font-size: 1rem;
    border-bottom: 1px solid color-mix(in srgb, var(--danger) 25%, transparent);
  }

  /* -- menu -- */
  .menu-body { flex: 1; min-height: 0; display: grid; grid-template-columns: 15rem minmax(0, 1fr); }
  .rail {
    display: flex; flex-direction: column; gap: 0.5rem; padding: 1.2rem 0.9rem; overflow-y: auto;
    background: var(--surface); border-right: 1px solid var(--border);
  }
  .cat {
    display: flex; align-items: center; gap: 0.9rem; width: 100%; text-align: left;
    padding: 0.9rem 1rem; border: 0; border-radius: 16px; background: transparent; cursor: pointer;
    font-size: 1.1rem; font-weight: 650; color: var(--ink-2);
  }
  .cat-icon {
    width: 2.8rem; height: 2.8rem; border-radius: 14px; display: grid; place-items: center; flex: none;
    background: var(--surface-2); color: var(--ink-2);
  }
  .cat-icon svg { width: 1.5rem; height: 1.5rem; }
  .cat-count { margin-left: auto; font-size: 0.85rem; color: var(--muted); font-weight: 600; }
  .cat[aria-current="true"] { background: var(--primary-soft); color: var(--ink); }
  .cat[aria-current="true"] .cat-icon { background: var(--primary); color: var(--primary-ink); }

  .grid-wrap { overflow-y: auto; padding: 1.4rem 1.6rem 2rem; scroll-behavior: smooth; }
  .group + .group { margin-top: 2rem; }
  .group-title { margin: 0 0 0.9rem; font-size: 1.35rem; font-weight: 800; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr)); gap: 1rem; }

  .card {
    position: relative; display: flex; flex-direction: column; gap: 0.35rem;
    padding: 1rem 1rem 1.1rem; border-radius: var(--radius); background: var(--surface);
    box-shadow: var(--shadow); cursor: pointer; transition: transform 0.08s ease, box-shadow 0.15s ease;
  }
  .card:active:not(.soldout) { transform: scale(0.98); }
  .card.in-cart { box-shadow: var(--shadow), inset 0 0 0 3px var(--primary); }
  .card .art { position: relative; display: grid; place-items: center; height: 9.5rem; margin-bottom: 0.3rem; }
  .card .drink-art { height: 9.5rem; max-width: 100%; width: auto; filter: drop-shadow(0 6px 8px rgba(28,26,22,0.15)); }
  /* foto's hebben een witte achtergrond: multiply laat die wegvallen tegen de lichte kaart */
  img.drink-art { object-fit: contain; mix-blend-mode: multiply; }
  .card img.drink-art { filter: none; }
  .card .name { margin: 0; font-size: 1.1rem; font-weight: 750; line-height: 1.2; min-height: 2.6rem; }
  .card .meta { font-size: 0.9rem; color: var(--muted); }
  .status { display: flex; align-items: center; gap: 0.45rem; font-size: 0.9rem; font-weight: 650; color: var(--good); }
  .status.low { color: var(--warn); }
  .status.out { color: var(--out); }
  .card-foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.5rem; margin-top: auto; padding-top: 0.5rem; min-height: 3.2rem; }
  .card .stepper { margin-left: auto; }
  .card .stepper button { width: 2.6rem; height: 2.6rem; }
  .card .stepper .q { min-width: 1.6rem; }
  .price { font-size: 1.2rem; font-weight: 800; }
  .add {
    width: 3.2rem; height: 3.2rem; border-radius: 50%; border: 0; cursor: pointer; flex: none;
    display: grid; place-items: center; background: var(--primary); color: var(--primary-ink);
  }
  .add svg { width: 1.5rem; height: 1.5rem; }
  .qty-badge {
    position: absolute; top: 0.7rem; right: 0.7rem; min-width: 2.2rem; height: 2.2rem; padding: 0 0.6rem;
    border-radius: 999px; display: grid; place-items: center; background: var(--primary); color: var(--primary-ink);
    font-weight: 800; font-size: 1.05rem;
  }
  .age-badge {
    position: absolute; top: 0.8rem; left: 0.8rem; padding: 0.2rem 0.55rem; border-radius: 8px;
    background: var(--ink); color: #fff; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.02em;
  }
  .card.soldout { cursor: default; box-shadow: none; background: color-mix(in srgb, var(--surface) 55%, var(--page)); }
  .card.soldout .drink-art { filter: grayscale(1); opacity: 0.35; }
  .card.soldout .name, .card.soldout .price { color: var(--muted); }
  .soldout-tag {
    position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%) rotate(-8deg);
    padding: 0.45rem 1rem; border-radius: 10px; background: var(--ink); color: #fff;
    font-size: 0.95rem; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; white-space: nowrap;
  }

  /* -- aantal kiezen -- */
  .stepper { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.25rem; border-radius: 999px; background: var(--surface-2); }
  .stepper button {
    width: 2.9rem; height: 2.9rem; border-radius: 50%; border: 0; cursor: pointer;
    display: grid; place-items: center; background: var(--surface); box-shadow: 0 1px 2px rgba(28,26,22,0.12);
  }
  .stepper button:disabled { opacity: 0.35; cursor: default; }
  .stepper button svg { width: 1.3rem; height: 1.3rem; }
  .stepper .q { min-width: 2rem; text-align: center; font-size: 1.25rem; font-weight: 800; }

  /* -- onderbalk met totaal -- */
  .orderbar {
    display: flex; align-items: center; gap: 1.2rem;
    padding: 1rem calc(1.6rem + env(safe-area-inset-right)) calc(1rem + env(safe-area-inset-bottom)) calc(1.6rem + env(safe-area-inset-left));
    background: var(--surface); border-top: 1px solid var(--border); box-shadow: 0 -8px 24px rgba(28,26,22,0.06);
  }
  .sum { flex: 1; display: flex; align-items: center; gap: 1rem; min-width: 0; }
  .bag { position: relative; width: 3.4rem; height: 3.4rem; border-radius: 16px; display: grid; place-items: center; background: var(--surface-2); flex: none; }
  .bag svg { width: 1.7rem; height: 1.7rem; }
  .bag-count {
    position: absolute; top: -0.45rem; right: -0.45rem; min-width: 1.6rem; height: 1.6rem; padding: 0 0.4rem;
    border-radius: 999px; display: grid; place-items: center; background: var(--primary); color: var(--primary-ink);
    font-size: 0.85rem; font-weight: 800;
  }
  .bag-count.bump { animation: bump 0.3s ease; }
  @keyframes bump { 50% { transform: scale(1.35); } }
  .sum-label { font-size: 0.95rem; color: var(--ink-2); }
  .sum-total { font-size: 1.6rem; font-weight: 800; }

  /* -- winkelmandje -- */
  .cart-wrap { flex: 1; min-height: 0; overflow-y: auto; padding: 1.4rem 1.6rem; }
  .cart-list { list-style: none; margin: 0 auto; padding: 0; max-width: 60rem; display: flex; flex-direction: column; gap: 0.8rem; }
  .row {
    display: grid; grid-template-columns: 4.5rem minmax(0, 1fr) auto 7rem 3rem; align-items: center; gap: 1.2rem;
    padding: 0.9rem 1.2rem; border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow);
  }
  .row .drink-art { height: 5.5rem; width: auto; justify-self: center; }
  .row-name { font-size: 1.2rem; font-weight: 750; }
  .row-meta { font-size: 0.9rem; color: var(--muted); margin-top: 0.15rem; }
  .row-total { text-align: right; font-size: 1.2rem; font-weight: 800; }
  .remove { color: var(--muted); }
  .cart-note { max-width: 60rem; margin: 1.2rem auto 0; color: var(--muted); font-size: 0.95rem; text-align: center; }
  .cart-error {
    max-width: 60rem; margin: 0 auto 1rem; padding: 0.9rem 1.2rem; border-radius: 14px;
    background: #fff1f0; color: var(--danger); font-weight: 650;
  }

  /* -- bevestiging -- */
  .done { align-items: center; justify-content: center; text-align: center; gap: 1rem; padding: 2rem; }
  .done-check {
    width: 7rem; height: 7rem; border-radius: 50%; display: grid; place-items: center;
    background: color-mix(in srgb, var(--good) 14%, var(--surface)); color: var(--good); margin-bottom: 0.5rem;
  }
  .done-check svg { width: 3.8rem; height: 3.8rem; }
  .done h1 { margin: 0; font-size: 3rem; font-weight: 800; }
  .done p { margin: 0; font-size: 1.3rem; color: var(--ink-2); }
  .order-no {
    margin: 1rem 0; padding: 1.2rem 3rem; border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow);
  }
  .order-no span { display: block; font-size: 1rem; color: var(--muted); font-weight: 650; text-transform: uppercase; letter-spacing: 0.08em; }
  .order-no b { display: block; font-size: 5rem; line-height: 1.1; font-weight: 800; }
  .done-count { margin-top: 1rem; font-size: 1rem !important; color: var(--muted) !important; }

  /* -- dialoog en melding -- */
  .modal-back { position: fixed; inset: 0; display: grid; place-items: center; padding: 1.5rem; background: rgba(20,18,14,0.45); z-index: 10; }
  .modal {
    width: min(32rem, 100%); padding: 2rem; border-radius: 26px; background: var(--surface);
    box-shadow: 0 20px 60px rgba(0,0,0,0.25); text-align: center;
  }
  .modal h2 { margin: 0 0 0.6rem; font-size: 1.7rem; font-weight: 800; }
  .modal p { margin: 0 0 1.6rem; font-size: 1.1rem; color: var(--ink-2); }
  .modal-actions { display: flex; gap: 0.8rem; justify-content: center; flex-wrap: wrap; }
  .toast {
    position: fixed; left: 50%; bottom: 7.5rem; transform: translateX(-50%); z-index: 20;
    padding: 0.9rem 1.4rem; border-radius: 999px; background: var(--ink); color: #fff;
    font-size: 1rem; font-weight: 650; box-shadow: 0 10px 30px rgba(0,0,0,0.25); max-width: calc(100% - 2rem);
  }

  /* -- staand scherm (zoals een echte bestelzuil) of smal venster -- */
  @media (max-aspect-ratio: 1/1), (max-width: 760px) {
    .menu-body { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto minmax(0, 1fr); }
    .rail { flex-direction: row; overflow-x: auto; overflow-y: hidden; border-right: 0; border-bottom: 1px solid var(--border); padding: 0.8rem 1rem; }
    .cat { width: auto; flex: none; padding: 0.6rem 1rem 0.6rem 0.6rem; }
    .cat-icon { width: 2.4rem; height: 2.4rem; }
    .cat-count { display: none; }
    .legend { display: none; }
    .welcome-title { font-size: 3.2rem; }
    .row { grid-template-columns: 3.5rem minmax(0, 1fr) auto; }
    .row .drink-art { height: 4.5rem; }
    .row-total { grid-column: 2; text-align: left; }
    .row .remove { grid-column: 3; justify-self: end; }
  }
  @media (max-width: 760px) {
    .orderbar { flex-wrap: wrap; }
    .orderbar .btn-secondary { order: 2; }
    .sum { flex-basis: 100%; }
    .grid { grid-template-columns: repeat(auto-fill, minmax(11.5rem, 1fr)); }
    .welcome-cans .drink-art { height: 6.5rem; }
  }
</style>
</head>
<body>
<!-- gedeelde glans voor alle blikjes -->
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs>
    <linearGradient id="canShine" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="#000" stop-opacity="0.28"/>
      <stop offset="0.28" stop-color="#fff" stop-opacity="0.38"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.32"/>
    </linearGradient>
  </defs>
</svg>

<section class="screen welcome" id="screen-welcome">
  <div class="welcome-hit" id="startBtn" role="button" tabindex="0" aria-label="Start je bestelling">
    <div class="welcome-cans" id="welcomeCans" aria-hidden="true"></div>
    <h1 class="welcome-title">Zin in iets fris?</h1>
    <p class="welcome-sub" id="welcomeSub">Kies je koude drankjes</p>
    <span class="welcome-cta">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V10"/><path d="M12 9.5a1.5 1.5 0 0 1 3 0v1"/><path d="M15 10.5a1.5 1.5 0 0 1 3 0V15a6 6 0 0 1-6 6h-.5a6 6 0 0 1-4.6-2.2L4.3 15.6a1.5 1.5 0 0 1 2.3-1.9L9 16"/></svg>
      Tik om te bestellen
    </span>
  </div>
  <div class="welcome-corner">
    <a class="ghost-btn" data-technical href="/technisch" title="Naar de technische bedieningsinterface">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>
      Technisch
    </a>
    <span class="credits" id="credits" hidden>Productfoto's: Open Food Facts (CC BY-SA)</span>
    <button class="ghost-btn" id="fsBtn" type="button">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3H5a2 2 0 0 0-2 2v3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M16 21h3a2 2 0 0 0 2-2v-3"/></svg>
      <span id="fsText">Volledig scherm</span>
    </button>
  </div>
</section>

<section class="screen" id="screen-menu" hidden>
  <header class="head">
    <div class="head-grow">
      <h1>Kies je drankjes</h1>
      <p>Tik op een drankje om het toe te voegen</p>
    </div>
    <div class="legend" aria-label="Uitleg beschikbaarheid">
      <span><span class="sdot"></span>Beschikbaar</span>
      <span><span class="sdot low"></span>Bijna op</span>
      <span><span class="sdot out"></span>Uitverkocht</span>
    </div>
    <a class="icon-btn" data-technical href="/technisch" title="Technische bediening" aria-label="Technische bediening">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>
    </a>
  </header>
  <div class="offline" data-offline hidden>Geen verbinding met de automaat. Bestellen kan op dit moment niet.</div>
  <div class="menu-body">
    <nav class="rail" id="rail" aria-label="Categorie&euml;n"></nav>
    <main class="grid-wrap" id="gridWrap"></main>
  </div>
  <footer class="orderbar">
    <button class="btn btn-secondary" id="cancelBtn" type="button">Annuleren</button>
    <div class="sum" aria-live="polite">
      <span class="bag" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 7h12l-1 13H7L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>
        <span class="bag-count num" id="bagCount">0</span>
      </span>
      <div>
        <div class="sum-label" id="sumLabel">Mijn bestelling</div>
        <div class="sum-total num" id="sumTotal">&euro; 0,00</div>
      </div>
    </div>
    <button class="btn btn-primary btn-lg" id="reviewBtn" type="button" disabled>
      Bestelling bekijken
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
    </button>
  </footer>
</section>

<section class="screen" id="screen-cart" hidden>
  <header class="head">
    <button class="btn btn-secondary" id="backBtn" type="button">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>
      Verder bestellen
    </button>
    <div class="head-grow"><h1>Controleer je bestelling</h1></div>
  </header>
  <div class="offline" data-offline hidden>Geen verbinding met de automaat. Bestellen kan op dit moment niet.</div>
  <main class="cart-wrap">
    <div class="cart-error" id="cartError" role="alert" hidden></div>
    <ul class="cart-list" id="cartList"></ul>
    <p class="cart-note" id="alcoholNote" hidden><strong>18+</strong> Je bestelling bevat alcohol. Bij het afhalen kan om legitimatie gevraagd worden.</p>
    <p class="cart-note">Betalen is nog niet nodig. Na het plaatsen wordt je bestelling klaargezet.</p>
  </main>
  <footer class="orderbar">
    <div class="sum">
      <div>
        <div class="sum-label" id="cartSumLabel">Totaal</div>
        <div class="sum-total num" id="cartTotal">&euro; 0,00</div>
      </div>
    </div>
    <button class="btn btn-primary btn-lg" id="placeBtn" type="button">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>
      <span id="placeText">Bestelling plaatsen</span>
    </button>
  </footer>
</section>

<section class="screen done" id="screen-done" hidden>
  <div class="done-check" aria-hidden="true">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>
  </div>
  <h1>Bedankt!</h1>
  <p>Je bestelling is ontvangen en wordt zo klaargezet.</p>
  <div class="order-no"><span>Bestelnummer</span><b class="num" id="orderNo">--</b></div>
  <button class="btn btn-primary btn-lg" id="doneBtn" type="button">Klaar</button>
  <p class="done-count" id="doneCount"></p>
</section>

<div class="modal-back" id="modal" hidden>
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <h2 id="modalTitle"></h2>
    <p id="modalText"></p>
    <div class="modal-actions">
      <button class="btn btn-secondary" id="modalSecondary" type="button"></button>
      <button class="btn btn-primary" id="modalPrimary" type="button"></button>
    </div>
  </div>
</div>
<div class="toast" id="toast" role="status" hidden></div>

<script>
const LOW_STOCK = 3;               // vanaf dit aantal of minder: "bijna op"
const IDLE_MS = 60000;             // zonder aanraking: vragen of de klant er nog is
const IDLE_GRACE_S = 20;           // daarna terug naar het startscherm
const DONE_RETURN_S = 10;          // bevestigingsscherm blijft zo lang staan
const MENU_POLL_MS = 5000;

const $ = id => document.getElementById(id);
const euro = new Intl.NumberFormat('nl-NL', {style: 'currency', currency: 'EUR'});
const money = cents => euro.format(cents / 100);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

const ICONS = {
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>',
  minus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"><path d="M5 12h14"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg>',
  alles: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>',
  frisdrank: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M8 4h8M7 6.5c0-1 .5-1.5 1.5-1.5h7c1 0 1.5.5 1.5 1.5v12c0 1-.5 1.5-1.5 1.5h-7C7.5 20 7 19.5 7 18.5z"/><path d="M7 10h10M7 15h10"/></svg>',
  icetea: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 6h12l-1.5 14h-9z"/><path d="M14 3l-2 7"/><rect x="9" y="11" width="3" height="3" rx=".6"/><rect x="12.5" y="14" width="3" height="3" rx=".6"/></svg>',
  energy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M13 3L5 14h6l-1 7 8-11h-6z"/></svg>',
  water: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3.5s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11z"/></svg>',
  bier: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M5 8h10v11a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 5 19z"/><path d="M15 10h2.5a1.5 1.5 0 0 1 1.5 1.5v4a1.5 1.5 0 0 1-1.5 1.5H15"/><path d="M5 8a2.5 2.5 0 0 1 2.5-4 3 3 0 0 1 5 0A2.5 2.5 0 0 1 15 8"/><path d="M8.5 12v5M11.5 12v5"/></svg>',
  seltzer: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="8" cy="16" r="3.5"/><circle cx="15.5" cy="10" r="2.5"/><circle cx="10" cy="6" r="1.5"/><circle cx="17" cy="18" r="1.5"/></svg>',
  overig: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 4l2.3 4.8 5.2.7-3.8 3.6.9 5.2L12 15.8l-4.6 2.5.9-5.2-3.8-3.6 5.2-.7z"/></svg>',
};

let menu = {categories: [], drinks: [], max_per_drink: 10};
let menuSig = '';
let online = true;
const cart = new Map();            // drink id -> aantal, in volgorde van toevoegen
let activeCategory = 'alles';
let screen = 'welcome';

const drinkById = id => menu.drinks.find(d => d.id === id);
const maxFor = d => Math.max(0, Math.min(d.stock, menu.max_per_drink));
const cartCount = () => [...cart.values()].reduce((a, b) => a + b, 0);
const cartTotal = () => [...cart].reduce((sum, [id, qty]) => sum + (drinkById(id)?.price_cents || 0) * qty, 0);
const isAlcohol = d => d.abv >= 0.5;
const drinkMeta = d => `${d.volume_ml} ml &middot; ${d.container}${d.abv ? ` &middot; ${String(d.abv).replace('.', ',')}%` : ''}`;

function drinkArt(d) {
  if (d.image) return `<img class="drink-art" src="${esc(d.image)}" alt="" draggable="false">`;
  return drinkSvg(d);
}

function drinkSvg(d) {
  const label = esc(d.label);
  if (d.container === 'fles') {
    const fit = d.label.length > 5 ? ' textLength="28" lengthAdjust="spacingAndGlyphs"' : '';
    return `<svg class="drink-art" viewBox="0 0 60 120" aria-hidden="true">
      <rect x="23" y="3" width="14" height="9" rx="2" fill="${d.accent}"/>
      <path d="M25 12H35V20Q46 26 46 38V108Q46 115 39 115H21Q14 115 14 108V38Q14 26 25 20Z" fill="${d.color}" fill-opacity="0.6" stroke="${d.color}" stroke-width="1.5"/>
      <rect x="14" y="58" width="32" height="26" fill="#fff"/>
      <rect x="14" y="58" width="32" height="4" fill="${d.accent}"/>
      <text x="30" y="77" text-anchor="middle" font-size="9" font-weight="800" fill="${d.ink}"${fit}>${label}</text>
      <path d="M19 36Q19 29 24 26" stroke="#fff" stroke-opacity="0.8" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    </svg>`;
  }
  const fit = d.label.length > 5 ? ' textLength="32" lengthAdjust="spacingAndGlyphs"' : '';
  const body = 'M11 15Q11 11 15 11H45Q49 11 49 15V105Q49 110 44 110H16Q11 110 11 105Z';
  return `<svg class="drink-art" viewBox="0 0 60 120" aria-hidden="true">
    <rect x="13" y="5" width="34" height="7" rx="3" fill="#cfd3d8"/>
    <path d="${body}" fill="${d.color}"/>
    <rect x="11" y="46" width="38" height="24" fill="${d.accent}"/>
    <text x="30" y="62" text-anchor="middle" font-size="10" font-weight="800" fill="${d.ink}"${fit}>${label}</text>
    <path d="${body}" fill="url(#canShine)"/>
    <rect x="14" y="108" width="32" height="6" rx="3" fill="#b8bcc2"/>
  </svg>`;
}

function statusHtml(d) {
  if (d.stock <= 0) return '<div class="status out"><span class="sdot out"></span>Uitverkocht</div>';
  if (d.stock <= LOW_STOCK) return `<div class="status low"><span class="sdot low"></span>Nog ${d.stock} beschikbaar</div>`;
  return '<div class="status"><span class="sdot"></span>Beschikbaar</div>';
}

function stepperHtml(d, qty) {
  return `<div class="stepper">
    <button type="button" data-act="dec" data-id="${d.id}" aria-label="E&eacute;n ${esc(d.name)} minder">${ICONS.minus}</button>
    <span class="q num">${qty}</span>
    <button type="button" data-act="inc" data-id="${d.id}" aria-label="E&eacute;n ${esc(d.name)} meer"${qty >= maxFor(d) ? ' disabled' : ''}>${ICONS.plus}</button>
  </div>`;
}

function cardHtml(d) {
  const qty = cart.get(d.id) || 0;
  const out = d.stock <= 0;
  let foot;
  if (out) foot = '';
  else if (qty > 0) foot = stepperHtml(d, qty);
  else foot = `<button class="add" type="button" data-act="inc" data-id="${d.id}" aria-label="${esc(d.name)} toevoegen">${ICONS.plus}</button>`;
  return `<article class="card${out ? ' soldout' : ''}${qty ? ' in-cart' : ''}" data-id="${d.id}"${out ? ' aria-disabled="true"' : ''}>
    <div class="art">${drinkArt(d)}${out ? '<span class="soldout-tag">Uitverkocht</span>' : ''}</div>
    <h3 class="name">${esc(d.name)}</h3>
    <div class="meta">${drinkMeta(d)}</div>
    ${statusHtml(d)}
    <div class="card-foot"><span class="price num">${money(d.price_cents)}</span>${foot}</div>
    ${qty ? `<span class="qty-badge num">${qty}</span>` : ''}
    ${isAlcohol(d) ? '<span class="age-badge">18+</span>' : ''}
  </article>`;
}

function renderRail() {
  const cats = [{id: 'alles', name: 'Alles'}, ...menu.categories];
  $('rail').innerHTML = cats.map(c => {
    const n = c.id === 'alles' ? menu.drinks.length : menu.drinks.filter(d => d.category === c.id).length;
    return `<button class="cat" type="button" data-cat="${c.id}" aria-current="${c.id === activeCategory}">
      <span class="cat-icon">${ICONS[c.id] || ICONS.overig}</span>${esc(c.name)}<span class="cat-count num">${n}</span>
    </button>`;
  }).join('');
}

function renderGrid() {
  const groups = activeCategory === 'alles'
    ? menu.categories
    : menu.categories.filter(c => c.id === activeCategory);
  const wrap = $('gridWrap');
  const scroll = wrap.scrollTop;
  wrap.innerHTML = groups.map(c => {
    const drinks = menu.drinks.filter(d => d.category === c.id);
    if (!drinks.length) return '';
    return `<section class="group"><h2 class="group-title">${esc(c.name)}</h2>
      <div class="grid">${drinks.map(cardHtml).join('')}</div></section>`;
  }).join('');
  wrap.scrollTop = scroll;
}

function renderSummary() {
  const count = cartCount();
  $('bagCount').textContent = count;
  $('sumTotal').textContent = money(cartTotal());
  $('sumLabel').textContent = count ? `Mijn bestelling (${count} ${count === 1 ? 'drankje' : 'drankjes'})` : 'Mijn bestelling';
  $('reviewBtn').disabled = count === 0;
}

function renderCart() {
  const count = cartCount();
  $('cartList').innerHTML = [...cart].map(([id, qty]) => {
    const d = drinkById(id);
    if (!d) return '';
    return `<li class="row">
      ${drinkArt(d)}
      <div><div class="row-name">${esc(d.name)}</div><div class="row-meta">${drinkMeta(d)} &middot; ${money(d.price_cents)} per stuk</div></div>
      ${stepperHtml(d, qty)}
      <div class="row-total num">${money(d.price_cents * qty)}</div>
      <button class="icon-btn remove" type="button" data-act="remove" data-id="${d.id}" aria-label="${esc(d.name)} verwijderen">${ICONS.trash}</button>
    </li>`;
  }).join('');
  $('cartSumLabel').textContent = `Totaal (${count} ${count === 1 ? 'drankje' : 'drankjes'})`;
  $('cartTotal').textContent = money(cartTotal());
  $('placeBtn').disabled = count === 0 || !online;
  $('alcoholNote').hidden = ![...cart.keys()].some(id => { const d = drinkById(id); return d && isAlcohol(d); });
}

function renderWelcome() {
  // Eerst van elke categorie een drankje, daarna aanvullen tot zes.
  const available = menu.drinks.filter(d => d.stock > 0);
  const shown = menu.categories.map(c => available.find(d => d.category === c.id)).filter(Boolean);
  for (const d of available) if (shown.length < 6 && !shown.includes(d)) shown.push(d);
  $('welcomeCans').innerHTML = shown.map(drinkArt).join('');
  $('credits').hidden = !menu.drinks.some(d => d.image);
  $('welcomeSub').textContent = available.length
    ? `Kies uit ${available.length} koude drankjes`
    : 'Kies je koude drankjes';
}

function renderAll() {
  renderWelcome();
  renderRail();
  renderGrid();
  renderSummary();
  renderCart();
}

function bump() {
  const el = $('bagCount');
  el.classList.remove('bump');
  void el.offsetWidth;
  el.classList.add('bump');
}

// Alcohol: eenmalig per klant vragen of die 18+ is (geldt tot de zuil opnieuw begint).
let ageConfirmed = false;
function confirmAge(onYes) {
  openModal({
    title: 'Ben je 18 jaar of ouder?',
    text: 'Alcoholhoudende dranken verkopen we alleen aan klanten van 18 jaar en ouder. Bij het afhalen kan om legitimatie gevraagd worden.',
    primary: 'Ja, ik ben 18+', secondary: 'Nee',
    onPrimary: () => { ageConfirmed = true; onYes(); },
    onSecondary: () => toast('Alcoholhoudende dranken zijn alleen voor 18 jaar en ouder'),
  });
}

function changeQty(id, delta) {
  const d = drinkById(id);
  if (!d) return;
  if (delta > 0 && isAlcohol(d) && !ageConfirmed && maxFor(d) > 0) {
    confirmAge(() => changeQty(id, delta));
    return;
  }
  const next = Math.max(0, Math.min(maxFor(d), (cart.get(id) || 0) + delta));
  if (delta > 0 && next === (cart.get(id) || 0)) {
    toast(maxFor(d) ? `Er zijn maximaal ${maxFor(d)} van ${d.name} beschikbaar` : `${d.name} is uitverkocht`);
    return;
  }
  if (next) cart.set(id, next); else cart.delete(id);
  if (delta > 0) bump();
  renderGrid();
  renderSummary();
  renderCart();
  if (screen === 'cart' && cart.size === 0) show('menu');
}

// Na een menu-update: verwijder of verminder wat niet meer beschikbaar is.
function clampCart() {
  const lost = [];
  for (const [id, qty] of cart) {
    const d = drinkById(id);
    const max = d ? maxFor(d) : 0;
    if (max <= 0) { cart.delete(id); lost.push(d ? d.name : id); }
    else if (qty > max) { cart.set(id, max); lost.push(d.name); }
  }
  if (lost.length) toast(`Aangepast, niet meer genoeg beschikbaar: ${lost.join(', ')}`);
}

async function loadMenu() {
  try {
    const response = await fetch('/api/kiosk/menu', {cache: 'no-store'});
    if (!response.ok) throw new Error(response.status);
    const data = await response.json();
    setOnline(true);
    const sig = JSON.stringify(data);
    if (sig === menuSig) return;
    menuSig = sig;
    menu = data;
    clampCart();
    renderAll();
  } catch (error) {
    setOnline(false);
  }
}

function setOnline(value) {
  if (online === value) return;
  online = value;
  document.querySelectorAll('[data-offline]').forEach(el => { el.hidden = online; });
  renderCart();
}

function show(name) {
  screen = name;
  for (const s of ['welcome', 'menu', 'cart', 'done']) $(`screen-${s}`).hidden = s !== name;
  if (name === 'cart') { $('cartError').hidden = true; renderCart(); }
  if (name === 'menu') $('gridWrap').scrollTop = 0;
}

function resetToWelcome() {
  cart.clear();
  ageConfirmed = false;
  activeCategory = 'alles';
  closeModal();
  clearInterval(doneTimer);
  renderAll();
  show('welcome');
}

// -- melding en dialoog --
let toastTimer = null;
function toast(text) {
  const el = $('toast');
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3200);
}

let modalHandlers = null;
function openModal({title, text, primary, secondary, onPrimary, onSecondary}) {
  $('modalTitle').textContent = title;
  $('modalText').textContent = text;
  $('modalPrimary').textContent = primary;
  $('modalSecondary').textContent = secondary;
  modalHandlers = {onPrimary, onSecondary};
  $('modal').hidden = false;
}
function closeModal() {
  $('modal').hidden = true;
  modalHandlers = null;
  clearInterval(idleTimer);
  idleTimer = null;
}
$('modalPrimary').addEventListener('click', () => { const h = modalHandlers; closeModal(); h?.onPrimary?.(); });
$('modalSecondary').addEventListener('click', () => { const h = modalHandlers; closeModal(); h?.onSecondary?.(); });

// -- geen aanraking: na IDLE_MS vragen of de klant er nog is --
let lastActivity = Date.now();
let idleTimer = null;
for (const ev of ['pointerdown', 'keydown']) document.addEventListener(ev, () => { lastActivity = Date.now(); }, true);
setInterval(() => {
  if ((screen === 'menu' || screen === 'cart') && !idleTimer && $('modal').hidden && Date.now() - lastActivity > IDLE_MS) {
    let left = IDLE_GRACE_S;
    const text = () => `Zonder reactie begint de zuil over ${left} seconden opnieuw.`;
    openModal({
      title: 'Ben je er nog?', text: text(),
      primary: 'Ja, verder bestellen', secondary: 'Opnieuw beginnen',
      onSecondary: resetToWelcome,
    });
    idleTimer = setInterval(() => {
      left -= 1;
      $('modalText').textContent = text();
      if (left <= 0) resetToWelcome();
    }, 1000);
  }
}, 1000);

// -- bestellen --
async function placeOrder() {
  if (!cart.size) return;
  $('placeBtn').disabled = true;
  $('placeText').textContent = 'Bezig...';
  $('cartError').hidden = true;
  try {
    const response = await fetch('/api/kiosk/order', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({items: [...cart].map(([id, qty]) => ({id, qty}))}),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      $('cartError').textContent = data.error || 'De bestelling kon niet geplaatst worden. Probeer het opnieuw.';
      $('cartError').hidden = false;
      await loadMenu();
      return;
    }
    cart.clear();
    renderAll();
    showDone(data.order_number);
  } catch (error) {
    $('cartError').textContent = 'Geen verbinding met de automaat. Probeer het opnieuw.';
    $('cartError').hidden = false;
  } finally {
    $('placeText').textContent = 'Bestelling plaatsen';
    renderCart();
  }
}

let doneTimer = null;
function showDone(number) {
  $('orderNo').textContent = String(number).padStart(3, '0');
  show('done');
  let left = DONE_RETURN_S;
  const text = () => `Terug naar het startscherm over ${left} seconden`;
  $('doneCount').textContent = text();
  clearInterval(doneTimer);
  doneTimer = setInterval(() => {
    left -= 1;
    $('doneCount').textContent = text();
    if (left <= 0) resetToWelcome();
  }, 1000);
}

// -- bediening --
function start() {
  activeCategory = 'alles';
  renderRail();
  renderGrid();
  show('menu');
}
$('startBtn').addEventListener('click', start);
$('startBtn').addEventListener('keydown', event => {
  if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); start(); }
});

$('rail').addEventListener('click', event => {
  const btn = event.target.closest('[data-cat]');
  if (!btn) return;
  activeCategory = btn.dataset.cat;
  renderRail();
  renderGrid();
  $('gridWrap').scrollTop = 0;
});

$('gridWrap').addEventListener('click', event => {
  const act = event.target.closest('[data-act]');
  if (act) {
    if (!act.disabled) changeQty(act.dataset.id, act.dataset.act === 'dec' ? -1 : 1);
    return;
  }
  const card = event.target.closest('.card');
  if (!card) return;
  if (card.classList.contains('soldout')) {
    toast(`${drinkById(card.dataset.id)?.name || 'Dit drankje'} is helaas uitverkocht`);
    return;
  }
  changeQty(card.dataset.id, 1);
});

$('cartList').addEventListener('click', event => {
  const act = event.target.closest('[data-act]');
  if (!act || act.disabled) return;
  const id = act.dataset.id;
  if (act.dataset.act === 'remove') changeQty(id, -(cart.get(id) || 0));
  else changeQty(id, act.dataset.act === 'dec' ? -1 : 1);
});

$('reviewBtn').addEventListener('click', () => show('cart'));
$('backBtn').addEventListener('click', () => show('menu'));
$('placeBtn').addEventListener('click', placeOrder);
$('doneBtn').addEventListener('click', resetToWelcome);
$('cancelBtn').addEventListener('click', () => {
  if (!cart.size) { resetToWelcome(); return; }
  openModal({
    title: 'Bestelling annuleren?',
    text: 'Je winkelmandje wordt leeggemaakt.',
    primary: 'Nee, verder bestellen', secondary: 'Ja, annuleren',
    onSecondary: resetToWelcome,
  });
});

// -- volledig scherm (alleen op het startscherm, voor de beheerder) --
const fsSupported = !!document.documentElement.requestFullscreen;
$('fsBtn').hidden = !fsSupported;
$('fsBtn').addEventListener('click', event => {
  event.stopPropagation();
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen().catch(() => {});
});
document.addEventListener('fullscreenchange', () => {
  $('fsText').textContent = document.fullscreenElement ? 'Venster' : 'Volledig scherm';
});
document.addEventListener('contextmenu', event => event.preventDefault());

loadMenu();
setInterval(loadMenu, MENU_POLL_MS);
</script>
</body>
</html>
"""

# Zelfde zuil zonder knoppen naar /technisch, voor kiosk_server.py (los van de machine).
STANDALONE_PAGE = KIOSK_PAGE.replace(
  "</style>", "  [data-technical] { display: none !important; }\n</style>", 1
)
