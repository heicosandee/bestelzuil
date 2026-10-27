"""Alleen de bestelzuil (kiosk.py), los van de machine.

Bedoeld om de zuil te testen of te delen (bijv. met de leverancier van de
kiosk-hardware): geen WAGO, geen FUYU, geen simulatie en geen technische
pagina. Bestellingen worden gecontroleerd en gelogd, net als in dashboard.py.

Start met: python3 kiosk_server.py [--host 0.0.0.0] [--port 8080]
Open dan: http://localhost:8080
Een deelbare zip maken: python3 export_kiosk.py
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import kiosk


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, content_type, status=200, cache=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if cache:
            self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status=200):
        self._send(json.dumps(obj).encode("utf-8"), "application/json", status)

    def do_GET(self):
        if self.path == "/":
            self._send(kiosk.STANDALONE_PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/api/kiosk/menu":
            self._json(kiosk.menu())
        elif self.path.startswith("/static/drinks/"):
            image = kiosk.drink_image(self.path[len("/static/drinks/"):])
            if image is None:
                self.send_error(404)
                return
            body, content_type = image
            self._send(body, content_type, cache="max-age=300")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/kiosk/order":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
            order = kiosk.place_order(data.get("items") if isinstance(data, dict) else None)
        except json.JSONDecodeError:
            self._json({"error": "Ongeldige bestelling."}, 400)
            return
        except kiosk.OrderError as e:
            self._json({"error": str(e)}, 409)
            return
        summary = ", ".join(f"{item['qty']}x {item['name']}" for item in order["items"])
        print(f"Bestelling {order['order_number']:03d}: {summary}", flush=True)
        self._json({"ok": True, "order_number": order["order_number"]})

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Bestelzuil zonder machine")
    parser.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = bereikbaar vanaf andere apparaten in het netwerk")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    shown = "localhost" if args.host in ("127.0.0.1", "0.0.0.0") else args.host
    print(f"Bestelzuil: http://{shown}:{args.port}  (Ctrl+C om te stoppen)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
