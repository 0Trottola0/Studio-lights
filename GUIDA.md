# Guida: installare o spostare Luci Ufficio su un altro PC

Questa guida serve a chi deve far girare l'app su un PC nuovo, che sia la prima installazione o lo spostamento da un altro computer. Non serve rifare la configurazione Tuya: **le chiavi delle lampadine sono legate alle lampadine, non al PC**.

---

## 0. Cosa ti serve

| Cosa | Dove si trova |
|---|---|
| Il codice dell'app | Il repository GitHub **0Trottola0/Studio-lights** (privato) |
| **`devices.json`** | Sul PC dove l'app gira oggi, nella cartella `smart-lights`. **Non è su GitHub** perché contiene le chiavi. |
| `tinytuya.json` (facoltativo) | Insieme a `devices.json`. Serve solo per rifare il wizard Tuya (vedi §7). |
| Un PC che resta acceso in ufficio | Sulla **stessa rete** delle lampadine |

> ⚠️ `devices.json` e `tinytuya.json` sono credenziali. Spostali con una chiavetta USB o un canale privato, **non** per email, chat o GitHub.

---

## 1. Sul vecchio PC: recupera i file

1. Copia **`devices.json`**, e se c'è **`tinytuya.json`**, dalla cartella `smart-lights` su una chiavetta.
2. Se sul vecchio PC c'è l'avvio automatico, disattivalo (vedi §6, "Disattivare").
3. Quando il nuovo PC funziona, **cancella** i due file dal vecchio PC.

---

## 2. Sul nuovo PC: installa Python

### Mac
Apri il **Terminale** e scrivi:
```bash
python3 --version
```
Se compare la richiesta di installare gli "strumenti per sviluppatori", accetta e aspetta che finisca.

### Windows
1. Scarica Python da **python.org/downloads**.
2. Nella prima schermata dell'installazione **spunta "Add python.exe to PATH"**, poi *Install Now*.
3. Apri **PowerShell** e verifica:
   ```powershell
   py --version
   ```

### Linux / Raspberry Pi
```bash
sudo apt install python3 python3-venv
```

---

## 3. Scarica l'app e installa la dipendenza

Metti la cartella `smart-lights` nella **cartella utente**: `~/smart-lights` su Mac e Linux, `C:\Users\<nome>\smart-lights` su Windows.
Su Mac evita Scrivania, Documenti e Download, perché l'avvio automatico potrebbe non avere i permessi per leggerli.

**Con git:**
```bash
git clone https://github.com/0Trottola0/Studio-lights.git ~/smart-lights
```

**Senza git:** apri **github.com/0Trottola0/Studio-lights** (da loggato, perché il repo è privato), scegli **Code → Download ZIP**, estrai lo zip e rinomina la cartella `Studio-lights-main` in `smart-lights`.

Poi installa `tinytuya`:

| Sistema | Comando |
|---|---|
| Mac | `python3 -m pip install --user tinytuya` |
| Windows | `py -m pip install tinytuya` |
| Linux / Raspberry Pi | `cd ~/smart-lights && python3 -m venv .venv && .venv/bin/pip install tinytuya` |

Su Linux, da qui in poi usa `.venv/bin/python` al posto di `python3`.

---

## 4. Copia le chiavi e verifica le lampadine

1. Copia **`devices.json`** dentro la cartella `smart-lights`.
2. Il nuovo PC può essere su un'altra rete, o le lampadine possono aver cambiato indirizzo. Aggiorna gli IP con:

   | Sistema | Comando |
   |---|---|
   | Mac | `cd ~/smart-lights && python3 aggiorna_ip.py` |
   | Windows | `cd $HOME\smart-lights; py aggiorna_ip.py` |
   | Linux | `cd ~/smart-lights && .venv/bin/python aggiorna_ip.py` |

   Ogni lampadina dovrebbe comparire con ✓. Una ✗ significa che è spenta dall'interruttore oppure che il PC non è sulla stessa rete.

---

## 5. Avvia e prova

| Sistema | Comando | In alternativa |
|---|---|---|
| Mac | `cd ~/smart-lights && python3 server.py` | doppio clic su `avvia.command` |
| Windows | `cd $HOME\smart-lights; py server.py` | doppio clic su `avvia.bat` |
| Linux | `cd ~/smart-lights && .venv/bin/python server.py` | |

- Se compare la richiesta del **firewall** (Mac o Windows), consenti l'accesso. Su Windows scegli **Reti private**.
- Apri **http://localhost:8000** sul PC per controllare che funzioni.
- Dal telefono usa l'indirizzo `http://192.168.…:8000` che il server stampa all'avvio.
- **Aggiorna l'icona sul telefono**: il PC è cambiato, quindi è cambiato anche l'indirizzo. Cancella la vecchia icona e rifai "Aggiungi alla schermata Home" con il nuovo indirizzo.

**PIN (consigliato in ufficio):**
- Mac e Linux: `LUCI_PIN=1234 python3 server.py`
- Windows: apri `avvia.bat` con il Blocco note e aggiungi la riga `set LUCI_PIN=1234` prima di `py server.py`.

---

## 6. Avvio automatico all'accensione

Così l'app riparte da sola dopo un riavvio, senza lasciare aperto il Terminale.

### Mac (launchd)
Incolla tutto il blocco nel Terminale. Per attivare il PIN, cambia `1234` con il PIN che vuoi; per non usarlo, lascia vuoto il valore tra `<string>` e `</string>`.
```bash
cd ~/smart-lights
cat > ~/Library/LaunchAgents/it.luciufficio.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>it.luciufficio</string>
  <key>ProgramArguments</key><array>
    <string>$(which python3)</string><string>$PWD/server.py</string>
  </array>
  <key>WorkingDirectory</key><string>$PWD</string>
  <key>EnvironmentVariables</key><dict><key>LUCI_PIN</key><string>1234</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$PWD/server.log</string>
  <key>StandardErrorPath</key><string>$PWD/server.log</string>
</dict></plist>
EOF
launchctl load ~/Library/LaunchAgents/it.luciufficio.plist
```
- Verifica aprendo http://localhost:8000. Se qualcosa non va, i messaggi sono in `~/smart-lights/server.log`.
- **Disattivare:**
  ```bash
  launchctl unload ~/Library/LaunchAgents/it.luciufficio.plist && rm ~/Library/LaunchAgents/it.luciufficio.plist
  ```
- **Non far andare il Mac in stop:** in Impostazioni di Sistema → Batteria (o Risparmio Energia) → *Impedisci lo stop automatico quando lo schermo è spento*.

### Windows
1. Premi **Win+R**, scrivi `shell:startup` e premi Invio. Si apre la cartella Esecuzione automatica.
2. Con il tasto destro su `avvia.bat` scegli **Crea collegamento**, poi sposta il collegamento in quella cartella.
3. Facoltativo: nelle proprietà del collegamento imposta **Esegui: Ridotta a icona**.
- **Disattivare:** cancella il collegamento da `shell:startup`.
- **Non far andare il PC in sospensione:** Impostazioni → Sistema → Alimentazione → Sospensione: **Mai** (con alimentazione collegata).
- Nota: il server parte quando l'utente **accede** a Windows, non prima.

### Linux / Raspberry Pi (systemd)
```bash
sudo tee /etc/systemd/system/luci.service >/dev/null <<EOF
[Unit]
Description=Luci Ufficio
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME/smart-lights
ExecStart=$HOME/smart-lights/.venv/bin/python server.py
Environment=LUCI_PIN=1234
Restart=always

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now luci
```
- Per vedere lo stato e i log: `systemctl status luci` e `journalctl -u luci -f`.
- **Disattivare:** `sudo systemctl disable --now luci`.

---

## 7. Consigli per un'installazione stabile

- **IP fisso per il PC server.** Nel router, nella sezione DHCP / "indirizzo riservato", assegna sempre lo stesso IP al PC. Così l'icona sul telefono non smette di funzionare.
- **IP fisso anche per le lampadine**, con lo stesso sistema: non dovrai più lanciare `aggiorna_ip.py`.
- **Reti aziendali:** se il telefono non apre la pagina ma il PC sì, la rete probabilmente isola i dispositivi tra loro (succede spesso con le reti "ospiti"). Serve l'IT, o una rete dedicata alle luci.

## 8. Quando serve rifare il wizard Tuya

Solo se **resetti o riassoci** una lampadina, o se ne **aggiungi una nuova**: la local key cambia o manca.
1. Copia `tinytuya.json` nella cartella `smart-lights`. Contiene Access ID e Secret, così non devi reinserirli.
2. Lancia `python3 -m tinytuya wizard` (su Windows `py -m tinytuya wizard`) dalla cartella `smart-lights`.
3. Se il portale Tuya segnala che il servizio *IoT Core* è scaduto, rinnovalo gratuitamente da **iot.tuya.com → Cloud → Cloud Services**.
4. Riavvia il server.

---

## Riepilogo veloce (trasloco su nuovo PC)

1. Copia `devices.json` dal vecchio PC su una chiavetta.
2. Sul nuovo PC: installa Python, scarica il repo in `~/smart-lights` e installa `tinytuya`.
3. Metti `devices.json` in `smart-lights` e lancia `aggiorna_ip.py`.
4. Avvia `server.py` e aprilo da http://localhost:8000.
5. Configura l'avvio automatico e disattiva la sospensione del PC.
6. Rifai l'icona sul telefono con il nuovo indirizzo.
7. Disattiva l'avvio automatico sul vecchio PC e cancella lì le chiavi.
