#!/usr/bin/env python3
"""Ritrova le lampadine sulla rete e aggiorna i loro indirizzi IP in devices.json.

Da usare quando sposti il server su un altro PC o rete, o quando una lampadina
risulta "Non raggiungibile". Non serve internet né l'account Tuya: le local key
restano quelle già presenti in devices.json.

Uso:  python3 aggiorna_ip.py      (su Windows:  py aggiorna_ip.py)
"""

import json
import shutil
import sys
from pathlib import Path

try:
    from tinytuya import scanner
except ImportError:
    sys.exit("Manca tinytuya. Installalo con:  python3 -m pip install --user tinytuya")

path = Path(__file__).resolve().parent / "devices.json"
if not path.exists():
    sys.exit("Non trovo %s: copialo qui prima di lanciare lo script." % path)

devices = json.loads(path.read_text())
ids = [d["id"] for d in devices if d.get("key") and not d.get("sub")]

print("Cerco %d dispositivi sulla rete (fino a ~20 secondi)..." % len(ids))
found = scanner.devices(verbose=False, poll=False, byID=True, color=False,
                        wantids=ids, scantime=18, assume_yes=True)

changed = 0
for d in devices:
    hit = found.get(d["id"])
    name = d.get("name") or d["id"]
    if not hit or not hit.get("ip"):
        if d["id"] in ids:
            print("  ✗ %-25s non trovata (accesa? stessa rete?)" % name)
        continue
    old = d.get("ip")
    d["ip"] = hit["ip"]
    if hit.get("version"):
        d["version"] = str(hit["version"])
    mark = "aggiornato" if old != d["ip"] else "invariato"
    changed += old != d["ip"]
    print("  ✓ %-25s %s (%s)" % (name, d["ip"], mark))

if changed:
    shutil.copy(path, path.with_suffix(".json.bak"))
    path.write_text(json.dumps(devices, indent=4))
    print("\nSalvato devices.json (copia del vecchio in devices.json.bak). Riavvia il server.")
else:
    print("\nNessun indirizzo cambiato.")
