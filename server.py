#!/usr/bin/env python3
"""Luci Ufficio: server minimale per comandare lampadine Tuya (es. Avatar) in rete locale.

Uso:
    python3 server.py                 # legge devices.json dalla cartella corrente
    LUCI_PIN=1234 python3 server.py   # opzionale: chiede un PIN per usare l'app
    LUCI_PORT=8080 python3 server.py  # opzionale: cambia porta (default 8000)

Dipendenze: solo `tinytuya` (python3 -m pip install --user tinytuya).
"""

import json
import os
import socket
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import tinytuya
except ImportError:
    sys.exit("Manca tinytuya. Installalo con:  python3 -m pip install --user tinytuya")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PORT = int(os.environ.get("LUCI_PORT", "8000"))
PIN = os.environ.get("LUCI_PIN", "").strip()

# Categorie Tuya che corrispondono a luci (dj = lampadina, dd/xdd = strisce, ecc.)
LIGHT_CATEGORIES = {"dj", "dd", "xdd", "fwd", "dc", "tgq", "tgkg"}


def find_devices_file():
    for candidate in (Path.cwd() / "devices.json", BASE_DIR / "devices.json"):
        if candidate.exists():
            return candidate
    sys.exit(
        "Non trovo devices.json.\n"
        "Copia nella cartella smart-lights il file devices.json creato da 'tinytuya wizard'."
    )


class Light:
    """Una lampadina, con lock per non sovrapporre comandi sulla stessa connessione."""

    def __init__(self, info):
        self.id = info["id"]
        self.name = info.get("name") or self.id
        self.lock = threading.Lock()
        version = info.get("version") or "3.3"
        self.dev = tinytuya.BulbDevice(
            dev_id=self.id,
            address=info.get("ip") or "Auto",
            local_key=info["key"],
            version=float(version),
        )
        self.dev.set_socketTimeout(3)
        self.dev.set_socketRetryLimit(1)

    def read_state(self):
        with self.lock:
            st = self.dev.state()
            if not isinstance(st, dict) or "Error" in st:
                err = st.get("Error") if isinstance(st, dict) else "nessuna risposta"
                return {"id": self.id, "name": self.name, "online": False, "error": str(err)}

            out = {
                "id": self.id,
                "name": self.name,
                "online": True,
                "on": bool(st.get("is_on")),
                "mode": st.get("mode"),
                "has_brightness": self.dev.bulb_has_capability("brightness"),
                "has_temp": self.dev.bulb_has_capability("colourtemp"),
                "has_colour": self.dev.bulb_has_capability("colour"),
            }
            try:
                if out["has_brightness"] and st.get("brightness") is not None:
                    out["brightness"] = round(self.dev.get_brightness_percentage(state=st))
                if out["has_temp"] and st.get("colourtemp") is not None:
                    out["temp"] = round(self.dev.get_colourtemp_percentage(state=st))
                if out["has_colour"] and st.get("colour"):
                    r, g, b = self.dev.colour_rgb(state=st)
                    out["colour"] = "#%02x%02x%02x" % (int(r), int(g), int(b))
            except Exception:  # valori parziali: meglio mostrare la lampadina che fallire
                pass
            return out

    def apply(self, cmd):
        action = cmd.get("action")
        with self.lock:
            if action == "power":
                res = self.dev.turn_on() if cmd.get("on") else self.dev.turn_off()
            elif action == "brightness":
                res = self.dev.set_brightness_percentage(clamp(cmd.get("value"), 1, 100))
            elif action == "white":
                res = self.dev.set_white_percentage(
                    brightness=clamp(cmd.get("brightness", 100), 1, 100),
                    colourtemp=clamp(cmd.get("temp", 50), 0, 100),
                )
            elif action == "colour":
                hexv = str(cmd.get("hex", "")).lstrip("#")
                if len(hexv) != 6:
                    raise ValueError("colore non valido")
                r, g, b = (int(hexv[i : i + 2], 16) for i in (0, 2, 4))
                res = self.dev.set_colour(r, g, b)
            else:
                raise ValueError("azione sconosciuta: %r" % action)
        if isinstance(res, dict) and "Error" in res:
            raise RuntimeError(res["Error"])


def clamp(value, lo, hi):
    return max(lo, min(hi, int(value)))


def load_lights():
    path = find_devices_file()
    data = json.loads(path.read_text())
    lights = {}
    for info in data:
        if not info.get("key") or info.get("sub"):
            continue
        cat = info.get("category")
        if cat and cat not in LIGHT_CATEGORIES:
            continue
        lights[info["id"]] = Light(info)
    if not lights:
        sys.exit("Nessuna lampadina trovata in %s" % path)
    return lights


LIGHTS = {}
POOL = ThreadPoolExecutor(max_workers=8)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, fmt, *args):  # log sintetico
        if "/api/" in self.path:
            sys.stderr.write("%s %s\n" % (self.command, self.path))

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        if not PIN or self.headers.get("X-Pin", "") == PIN:
            return True
        self._json(401, {"error": "PIN richiesto"})
        return False

    def do_GET(self):
        if self.path.startswith("/api/"):
            if not self._authorized():
                return
            if self.path == "/api/lights":
                states = list(POOL.map(safe_state, LIGHTS.values()))
                return self._json(200, {"lights": states})
            if self.path.startswith("/api/lights/"):
                light = LIGHTS.get(self.path.rsplit("/", 1)[-1])
                if not light:
                    return self._json(404, {"error": "lampadina non trovata"})
                return self._json(200, safe_state(light))
            return self._json(404, {"error": "non trovato"})
        return super().do_GET()

    def do_POST(self):
        if not self._authorized():
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            cmd = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json(400, {"error": "JSON non valido"})

        if self.path == "/api/all":
            # Comando a tutte le lampadine in parallelo (es. tutto acceso / spento)
            results = list(POOL.map(lambda l: safe_apply(l, cmd), LIGHTS.values()))
            return self._json(200, {"results": results})

        if self.path.startswith("/api/lights/"):
            light = LIGHTS.get(self.path.rsplit("/", 1)[-1])
            if not light:
                return self._json(404, {"error": "lampadina non trovata"})
            res = safe_apply(light, cmd)
            return self._json(200 if res["ok"] else 502, res)

        return self._json(404, {"error": "non trovato"})


def safe_state(light):
    try:
        return light.read_state()
    except Exception as exc:
        return {"id": light.id, "name": light.name, "online": False, "error": str(exc)}


def safe_apply(light, cmd):
    try:
        light.apply(cmd)
        return {"id": light.id, "ok": True}
    except Exception as exc:
        return {"id": light.id, "ok": False, "error": str(exc)}


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    LIGHTS.update(load_lights())
    try:
        server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    except OSError:
        sys.exit(
            "La porta %d è già in uso (il server è già avviato?).\n"
            "Chiudi l'altro server o usa un'altra porta:  LUCI_PORT=8080 python3 server.py" % PORT
        )
    print("Lampadine caricate: %d" % len(LIGHTS))
    for light in LIGHTS.values():
        print("  - %s" % light.name)
    print("\nApri dal PC:       http://localhost:%d" % PORT)
    print("Apri dal telefono: http://%s:%d  (stessa rete Wi-Fi)" % (local_ip(), PORT))
    if PIN:
        print("PIN attivo.")
    print("Ctrl+C per fermare.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nFermato.")


if __name__ == "__main__":
    main()
