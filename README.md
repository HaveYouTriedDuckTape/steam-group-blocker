```markdown
# Steam Group Members Blocker

Ein CLI‑Tool, das Mitglieder einer Steam‑Gruppe über den XML‑Feed einliest und anschließend wahlweise blockiert oder wieder entblockt – mit .env‑Cookies, TOML‑Konfiguration, optionaler Parallelisierung und einer kompakten, einzeiligen Rich‑Progress‑Anzeige (Fetch + Block).

> Hinweis: Der Einsatz erfolgt auf eigenes Risiko. Cookies enthalten Zugangsdaten; sicher und vertraulich behandeln. Die Nutzung sollte den Bedingungen der jeweiligen Plattform entsprechen.

## Features

- Blockieren oder Entblocken pro Nutzer (konfigurierbarer Modus).
- Mitgliederlisten aus dem memberslistxml‑Feed mit Frühabbruch:
  - Stop, sobald genug IDs gesammelt sind (max_per_group).
  - Stop, wenn eine Seite weniger als 1000 IDs liefert.
- Ein kombinierter, kompakter Progress‑Balken (Rich) für Fetch und Block:
  - „Modus • Gruppe • Seiten x/y • ids:n • ok:n • err:n“.
- Optionale Parallelisierung beim Blocken (Thread‑Pool).
- Fehlertoleranz:
  - Bei HTTP/Netzwerkfehlern 15 Sekunden Pause, kurze Erklärung, Rückfrage zum Abbruch (Timeout 15 Sekunden – ohne Eingabe wird fortgesetzt).

## Voraussetzungen

- Python 3.11+ (wegen tomllib in der Standardbibliothek).
- Betriebssystem: Linux, macOS oder Windows.
- Ein Steam‑Account mit gültigen Community‑Cookies (sessionid, steamLoginSecure).

## Installation

Empfohlen: virtuelles Environment.

```
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
# Windows (PowerShell)
. .venv\Scripts\Activate.ps1

pip install -r requirements.txt
# Falls keine requirements.txt vorhanden:
pip install requests python-dotenv rich
```

Optionale Datei requirements.txt:
```
requests>=2.31.0
python-dotenv>=1.0.1
rich>=13.7
```

## Konfiguration

### 1) .env

Legt die Cookies des eingeloggten Kontos ab (nicht ins Repo committen):

```
SESSIONID=your_sessionid_cookie_value
STEAMLOGINSECURE=your_steamLoginSecure_cookie_value
```

### 2) config.toml

Hauptkonfiguration für Quellen, Limits, Modus, Parallelität und Logging:

```
[general]
# EINE Option setzen:
groups_file = "groups.txt"                 # Datei mit Gruppen-URLs (eine pro Zeile)
# group_url = "https://steamcommunity.com/groups/afd-esport"

max_per_group = 500                        # 0 = alle Mitglieder
dry_run = false                            # true = nur IDs ausgeben, nichts blocken
log_level = "INFO"                         # DEBUG | INFO | WARNING | ERROR

[cookies]
use_env = true                             # Cookies aus .env nutzen
# Alternativ direkt setzen (nur wenn use_env=false):
# sessionid = ""
# steamLoginSecure = ""

[block]
mode = "block"                             # "block" oder "unblock"
concurrency = 4                            # parallele Block-POSTs (1 = sequentiell)
referer = "group"                          # "group" oder "profile"
```

Beispiel für groups.txt:
```
https://steamcommunity.com/groups/afd-esport
# Kommentare werden ignoriert
```

## Nutzung

Standard (nutzt ./config.toml und .env):

```
python main.py
```

Alternativ einen anderen Pfad zur Konfiguration setzen:

```
CONFIG_PATH=./path/to/config.toml python main.py
# Windows (PowerShell):
# $env:CONFIG_PATH=".\path\to\config.toml"; python .\main.py
```

Trockentest (IDs sammeln, nichts blocken):
- In config.toml: dry_run = true
- Oder temporär max_per_group auf einen kleinen Wert setzen (z. B. 10)

## Was das Tool tut

- Phase 1 (Fetch):
  - Liest den memberslistxml‑Feed seitenweise.
  - Zählt Seiten (p/x), sammelt IDs, bricht früh ab, wenn:
    - das Limit erreicht ist (max_per_group),
    - oder die aktuelle Seite weniger als 1000 IDs enthält (letzte Seite).
- Phase 2 (Block/Unblock):
  - Sendet für jede SteamID einen POST an den Web‑Action‑Endpoint.
  - Nutzt „sessionID“ im Formular‑Body und setzt cookies (sessionid, steamLoginSecure).
  - Fortschritt erhöht ok/err und zeigt Restzeit an.

## Fehlerbehandlung

- Bei HTTP/Netzwerkfehlern:
  - 15 Sekunden Pause.
  - Kompakte Fehlerhinweise (Status/Grund, kurze Body‑Vorschau).
  - Interaktive Rückfrage „Abbrechen?“ mit 15 Sekunden Timeout.
  - Ohne Eingabe: automatische Fortsetzung.
- Nach einem Lauf mit Fehlern wird eine Datei failed-<timestamp>.txt mit betroffenen IDs erzeugt (optional).

## Sicherheit & Hinweise

- .env niemals in die Versionskontrolle einchecken (in .gitignore aufnehmen).
- Cookies verfallen oder ändern sich; bei 400/403 erneut aktuelle Cookies aus dem Browser übernehmen.
- Parallelität moderat wählen (z. B. 2–4). Zu hohe Werte können Fehler (429/403) provozieren.

## Beispielausgabe (kompakt)

```
BLK https://steamcommunity.com/groups/afd-esport
BLK -  https://steamcommunity.com/groups/afd-es… -  p:3/17 -  ids:2431 -  ok:0 -  err:0  ━━━━━━━ 18%  ETA 0:43
…
BLK -  https://steamcommunity.com/groups/afd-es… -  p:17/17 -  ids:16766 -  ok:500 -  err:2 ━━━━━━━ 100%  ETA 0:00
Fertig: sel=500 ok=498 err=2
```

## Projektstruktur (empfohlen)

```
.
├─ main.py
├─ config.toml
├─ .env
├─ groups.txt
├─ requirements.txt
└─ README.md
```

## Lizenz

MIT‑Lizenz (siehe LICENSE).

## Beitrag

- Issues und Pull Requests sind willkommen (Fehlerberichte, Verbesserungen, Dokumentation).
- Bitte sensible Daten (Cookies, IDs) nicht in Issues posten.

```

[1](https://github.com/othneildrew/Best-README-Template)
[2](https://realpython.com/readme-python-project/)
[3](https://git.ifas.rwth-aachen.de/templates/ifas-python-template/-/blob/master/README.md)
[4](https://github.com/lincc-frameworks/python-project-template)
[5](https://dev.to/sumonta056/github-readme-template-for-personal-projects-3lka)
[6](https://github.com/alan-turing-institute/python-project-template)
[7](https://github.com/catiaspsilva/README-template)
[8](https://www.youtube.com/watch?v=12trn2NKw5I)
[9](https://www.makeareadme.com)
[10](https://github.com/saezlab/python-project)
[11](https://iopscience.iop.org/article/10.3847/2515-5172/ad4da1)
[12](https://arxiv.org/abs/2503.04921)
[13](http://thesai.org/Publications/ViewPaper?Volume=15&Issue=11&Code=ijacsa&SerialNo=110)
[14](https://ieeexplore.ieee.org/document/10633301/)
[15](http://ksiresearch.org/seke/seke21paper/paper162.pdf)
[16](https://jds-online.org/doi/10.6339/22-JDS1059)
[17](https://www.semanticscholar.org/paper/c23c5014583b7fcb96db7abd17e3ab0b39f55b58)
[18](https://academic.oup.com/nar/article/50/W1/W753/6582172)
[19](http://biorxiv.org/lookup/doi/10.1101/789842)
[20](https://ieeexplore.ieee.org/document/10931854/)
