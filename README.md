Open `bestelzuil.html` direct in de browser (geen server nodig), of volg de instructies hieronder.


Drinks kiosk - ordering screen (standalone test build)
=====================================================

Build: bestelzuil-20261012-bba7961

This is only the customer-facing ordering screen of the drinks vending
machine. It runs without the machine: no robot or hardware is connected,
so it is safe to run anywhere. The screen is in Dutch.

Requirements
------------
Python 3.7 or newer (https://www.python.org/downloads/). No other packages.

Start
-----
  Windows:        double-click start-windows.bat
  macOS / Linux:  ./start-mac-linux.sh    (or: python3 kiosk_server.py)

Then open http://localhost:8080 in the browser on the same device.
Stop with Ctrl+C (or close the window).

Options
-------
  --port 9000       use another port
  --host 0.0.0.0    also reachable from other devices in the network, e.g.
                    run it on a laptop and open http://<laptop-ip>:8080 on
                    the kiosk. Allow the port in the firewall if needed.

Full-screen kiosk mode (Chrome / Chromium / Edge), for example:
  chrome --kiosk --noerrdialogs --disable-pinch --overscroll-history-navigation=0 http://localhost:8080
The welcome screen also has a "Volledig scherm" (full screen) button.

What to expect
--------------
- Tap the welcome screen, pick drinks, confirm; you get an order number.
- Drinks with alcohol ask the customer to confirm they are 18+.
- After 60 s without touch it asks whether the customer is still there and
  returns to the welcome screen 20 s later.
- If the server is stopped, the screen shows a "no connection" banner and
  recovers by itself once the server is back.
- Test build limits: the assortment and stock are fixed sample data, stock
  does not go down, order numbers restart at 001 when the server restarts.
  Placed orders are printed in the server window.

Credits
-------
Product photos: Open Food Facts, CC BY-SA 3.0 (see static/drinks/CREDITS.md).
