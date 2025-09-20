# Steam Group Members Blocker (Python)

Dieses Werkzeug liest Mitglieder einer Steam‑Gruppe über den offiziellen XML‑Feed ein und blockiert oder entblockt die gefundenen Accounts – konfigurierbar, mit .env‑Cookies, TOML‑Konfiguration, optionaler Parallelisierung und einer kompakten Rich‑Progress‑Anzeige.

Wichtig
- Nutzung auf eigenes Risiko. Cookies sind vertraulich zu behandeln.
- Bitte die Regeln und Bedingungen der betroffenen Plattform beachten.

---

## Schnellstart (TL;DR)

1) Python 3.11+ installieren.  
2) Projekt entpacken/klonen und Terminal im Projektordner öffnen.  
3) Virtuelle Umgebung anlegen und aktivieren.  
4) Abhängigkeiten installieren.  
5) .env und config.toml füllen.  
6) Skript starten.

Beispiel:
```
python -m venv .venv
# macOS/Linux
. .venv/bin/activate
# Windows (PowerShell)
. .venv\Scripts\Activate.ps1

pip install -r requirements.txt  # oder: pip install requests python-dotenv rich
python main.py
```

---

## Voraussetzungen

- Betriebssystem: Windows, macOS oder Linux  
- Python: Version 3.11 oder neuer  
- Internetzugang  
- Ein Steam‑Account mit gültigen Community‑Cookies:
  - sessionid
  - steamLoginSecure

---

## Installation

### 1) Projekt vorbereiten
- Code in einen lokalen Ordner kopieren/klonen, z. B. C:\Projekte\steam-blocker oder ~/Projects/steam-blocker.

### 2) Virtuelle Umgebung
```
python -m venv .venv
# macOS/Linux
. .venv/bin/activate
# Windows (PowerShell)
. .venv\Scripts\Activate.ps1
```

### 3) Abhängigkeiten
Entweder mit requirements.txt:
```
pip install -r requirements.txt
```

Oder manuell:
```
pip install requests python-dotenv rich
```

Optionale requirements.txt:
```
requests>=2.31.0
python-dotenv>=1.0.1
rich>=13.7
```

---

## Konfiguration

Das Skript liest Einstellungen aus zwei Dateien im Projektordner: .env und config.toml.

### 1) .env (vertraulich!)
- Nicht in die Versionskontrolle committen.
- Enthält die beiden Cookies des eingeloggten Browsers (Domain: steamcommunity.com).

Beispiel (.env):
```
SESSIONID=your_sessionid_cookie_value
STEAMLOGINSECURE=your_steamLoginSecure_cookie_value
```

Woher kommen die Werte?
- Im eingeloggten Browser (z. B. Chrome/Firefox) die Website mit Community‑Bereich öffnen.
- In den Entwicklertools die Cookies für steamcommunity.com ansehen.
- Die Werte von „sessionid“ und „steamLoginSecure“ kopieren (ohne Anführungszeichen) und hier einfügen.

Tipp: Cookies verfallen. Bei Fehlern (z. B. 400/403) ggf. neue Werte aus dem Browser holen.

### 2) config.toml
- Gesamtsteuerung: Quelle(n), Limit, Modus, Parallelität, Logging.

Beispiel (config.toml):
```
[general]
# Entweder groups_file ODER group_url setzen:
groups_file = "groups.txt"                 # Datei mit Gruppen-URLs (eine pro Zeile)
# group_url = "https://steamcommunity.com/groups/afd-esport"

max_per_group = 500                        # 0 = alle Mitglieder der Gruppe
dry_run = false                            # true = nur IDs sammeln/anzeigen, nichts blocken
log_level = "INFO"                         # DEBUG | INFO | WARNING | ERROR

[cookies]
use_env = true                             # Cookies aus .env verwenden
# Alternativ direkt setzen, falls use_env=false:
# sessionid = ""
# steamLoginSecure = ""

[block]
mode = "block"                             # "block" oder "unblock"
concurrency = 4                            # parallele Block-POSTs (1 = sequentiell, 2–4 empfohlen)
referer = "group"                          # "group" oder "profile" (Referer-Header)
```

Beispiel (groups.txt):
```
https://steamcommunity.com/groups/afd-esport
# Kommentare (Zeilen beginnend mit #) werden ignoriert
```

---

## Nutzung

Standardaufruf (nutzt ./config.toml und .env):
```
python main.py
```

Konfigurationspfad explizit setzen:
```
# macOS/Linux
CONFIG_PATH=./pfad/zu/config.toml python main.py

# Windows (PowerShell)
$env:CONFIG_PATH=".\pfad\zu\config.toml"; python .\main.py
```

Typische Arbeitsweise:
1) Erst „dry_run = true“ setzen und Start testen (Sammeln/Anzeige der IDs ohne Änderungen).  
2) max_per_group z. B. auf 100–500 setzen, um gezielt zu testen.  
3) „dry_run = false“ setzen, um den Modus „block“ oder „unblock“ auszuführen.  
4) concurrency anfangs konservativ (z. B. 2–4) halten.

Ausgabe:
- Ein kompakter, kombinierter Fortschrittsbalken zeigt:
  - Modus (BLK/UNBLK)
  - Gruppe (gekürzt)
  - Seitenfortschritt (p:x/y)
  - Anzahl gesammelter IDs (ids)
  - Erfolgreich geblockte/entblockte (ok)
  - Fehler (err)
- Nach Abschluss wird eine kurze Zusammenfassung geloggt.

---

## Beispiele

Nur IDs sammeln (Dry‑Run):
- In config.toml: dry_run = true
- Start:
```
python main.py
```

500 Mitglieder blocken, parallele Anfragen:
- config.toml:
```
[general]
max_per_group = 500
dry_run = false

[block]
mode = "block"
concurrency = 4
```
- Start:
```
python main.py
```

Entblocken:
- config.toml:
```
[block]
mode = "unblock"
```

---

## Fehler & Lösungen (Kurz)

- 400 Client Error:
  - Meist „sessionID“/Cookies ungültig oder abgelaufen.
  - Neue Cookie‑Werte aus dem Browser übernehmen.

- 403 Forbidden oder 429 Too Many Requests:
  - Parallelität reduzieren (concurrency kleiner wählen).
  - Kurze Pause einlegen und erneut versuchen.

- 503 Service Unavailable:
  - Dienst temporär überlastet. Später erneut versuchen.

- Interaktive Fehlerbehandlung:
  - Bei Fehlern pausiert das Skript 15 Sekunden, zeigt eine kurze Erklärung und fragt, ob abgebrochen werden soll.
  - Ohne Antwort innerhalb von 15 Sekunden läuft das Skript automatisch weiter.

---

## Häufige Fragen (FAQ)

- Werden Freunde übersprungen?
  - Aktuell: Nein. Das Skript arbeitet rein ID‑basiert. Bei Bedarf vorher ID‑Listen filtern.

- Kann man mehrere Gruppen in einem Lauf verarbeiten?
  - Ja, per groups_file. Jede Zeile eine Gruppen‑URL.

- Werden alle Mitglieder der Gruppe geladen?
  - Ja, seitenweise. Das Skript bricht früh ab, wenn:
    - max_per_group erreicht ist, oder
    - eine Seite weniger als 1000 IDs liefert (typische letzte Seite des Feeds).

- Wie sicher sind die Cookies?
  - Cookies sind geheimnisgleich zu behandeln. .env niemals veröffentlichen.

---

## Deinstallation / Aufräumen

Virtuelle Umgebung löschen:
- Den Ordner .venv einfach entfernen.

Abhängigkeiten entfernen:
- Wenn keine virtuelle Umgebung genutzt wurde, ggf. manuell deinstallieren oder ein frisches venv anlegen.

Konfigurations‑/Hilfsdateien:
- .env, config.toml, groups.txt nach Bedarf behalten oder löschen.

---

## Hinweise für Fortgeschrittene

- Logging:
  - log_level auf DEBUG schalten, um detailliertere Meldungen zu erhalten.
- Performance:
  - concurrency moderat erhöhen, aber bei Fehlern wieder senken.
- Anpassungen:
  - Referer „group“ vs. „profile“ kann je nach Umgebung Unterschiede machen.

---

## Lizenz

MIT (empfohlen). Bitte LICENSE im Repository ergänzen.

## Beiträge

- Issues und Pull Requests willkommen (Fehler, Verbesserungen, Dokumentation).
- Bitte keine sensiblen Daten (Cookies, private IDs) in öffentlichen Tickets posten.
