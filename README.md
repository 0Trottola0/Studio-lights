# Luci Ufficio

App leggerissima per comandare le lampadine **Avatar** (e in generale qualunque lampadina **Tuya / Smart Life**) dalla rete locale, senza cloud.

- **Server**: un solo file Python (`server.py`). L'unica dipendenza è `tinytuya`.
- **App**: una pagina web (`static/index.html`) da aprire su telefono o PC e da aggiungere alla schermata home.
- **Funzioni**: accensione e spegnimento, luminosità, bianco caldo/freddo, colori.
- **Tutte insieme**: la scheda "Tutte le lampadine" in cima imposta accensione, intensità, bianco o colore su tutte con un solo gesto. Il pulsante "Copia su tutte" di ogni lampadina replica le sue impostazioni su tutte le altre.

```
Telefono / PC  ──http──▶  server.py (Mac in ufficio)  ──Tuya locale──▶  lampadine
```

> 📘 Installare o spostare l'app su un altro PC (Mac, Windows, Linux) e configurare l'avvio automatico: vedi **[GUIDA.md](GUIDA.md)**.

## Avvio (Mac)

1. Scarica il repo (vedi [GUIDA.md](GUIDA.md), §3) e copia nella cartella il file **`devices.json`** creato da `tinytuya wizard`.
2. Installa la dipendenza, una volta sola:

   ```bash
   python3 -m pip install --user tinytuya
   ```

3. Avvia il server dalla cartella `smart-lights`:

   ```bash
   cd smart-lights
   python3 server.py
   ```

   Se macOS chiede di consentire le connessioni in entrata a Python, clicca **Consenti**.

4. Apri l'app:
   - **dal Mac**: http://localhost:8000
   - **dal telefono**, collegato allo **stesso Wi-Fi**: usa l'indirizzo `http://192.168.x.x:8000` che il server stampa all'avvio.

   Sul telefono, con **Condividi → Aggiungi alla schermata Home** (iPhone) o **⋮ → Aggiungi a schermata Home** (Android), ottieni un'icona come un'app vera.

## Opzioni

| Variabile | A cosa serve | Esempio |
|---|---|---|
| `LUCI_PIN` | Chiede un PIN prima di usare l'app (utile in ufficio) | `LUCI_PIN=4821 python3 server.py` |
| `LUCI_PORT` | Cambia la porta, default 8000 | `LUCI_PORT=8080 python3 server.py` |

## Problemi comuni

- **"Non raggiungibile"**
  - La lampadina è spenta dall'interruttore a muro.
  - Oppure ha cambiato indirizzo IP. In questo caso rilancia `python3 -m tinytuya scan` e aggiorna `devices.json`, oppure fissa l'IP delle lampadine nel router (DHCP reservation).
- **Dal telefono non si apre**: telefono e Mac devono essere sulla stessa rete. Alcune reti aziendali o "ospiti" isolano i dispositivi tra loro: in quel caso serve l'IT, o una rete dedicata.
- **Lampadine resettate o riassociate**: la local key cambia, quindi bisogna rilanciare `python3 -m tinytuya wizard`.

## Sicurezza

`devices.json` e `tinytuya.json` contengono le chiavi delle lampadine: sono esclusi da git tramite `.gitignore`. Non vanno condivisi.
