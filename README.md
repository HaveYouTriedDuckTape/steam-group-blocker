# Steam Group Members Blocker

Einfaches Tool das automatisch alle Mitglieder der Steam-AfD-Gruppen bei Steam blockieren

## 1) Download & Ordner öffnen
- Auf GitHub den grünen „Code“-Button klicken → „Download ZIP“ wählen und das ZIP entpacken.  
- Im entpackten Ordner PowerShell öffnen

## 2) Python einrichten
- Python 3.11+ für Windows installieren: https://www.python.org/downloads/windows/ (Häkchen „Add Python to PATH“ setzen).  
- Abhängigkeiten installieren:
  ```
  py -m pip install -r requirements.txt
  ```
  Falls die Datei fehlt:
  ```
  py -m pip install --user requests python-dotenv rich
  ```

## 3a) Cookies eintragen - Version A: .env-Datei
- Im Browser bei steamcommunity.com angemeldet sein, dann Entwicklerwerkzeuge (F12) → „Application/Storage“ → „Cookies“ → `https://steamcommunity.com`.

  <img width="765" height="345" alt="68747470733a2f2f692e696d6775722e636f6d2f3238636b5852622e706e67" src="https://github.com/user-attachments/assets/9c68e94a-0a08-411e-8ccb-1fb6d8608259" />

- Im Projektordner eine Datei `.env` anlegen. (Einfache eine Textdatei anlegen und in ".env" umbenennen)
- Die Werte `sessionid` und `steamLoginSecure` in die .env-Datei kopieren und so eintragen:
  ```
  SESSIONID=hier_deine_sessionid
  STEAMLOGINSECURE=hier_dein_steamLoginSecure
  ```
## 3b) Cookies eintragen - Version B: config.toml
- config.toml von:
  ```
  [cookies]
  # Cookies aus .env laden (SESSIONID, STEAMLOGINSECURE) oder hier explizit setzen
  use_env = true
  # sessionid = ""
  # steamLoginSecure = ""
  ```
- Zu folgendem ändern:
  ```
  [cookies]
  # Cookies aus .env laden (SESSIONID, STEAMLOGINSECURE) oder hier explizit setzen
  use_env = false
  sessionid = "2134ik14jtjn14ik12"
  steamLoginSecure = "134124oogo1o1313o1"
  ```

## 4) Gruppenliste prüfen (groups.txt)
- Die Datei `groups.txt` ist bereits im Repository vorhanden.  
- Jede Zeile enthält genau eine Gruppen‑URL, z. B.:
  ```
  https://steamcommunity.com/groups/afd-esport
  ```
- Weitere Gruppen hinzufügen = neue Zeilen anhängen, vorhandene Einträge können bearbeitet werden.

## 5) Start
- PowerShell im Ordner:
  ```
  python .\steam-group-blocker.py
  ```
- Während der Ausführung zeigt das Tool einen kompakten Fortschrittsbalken (Seiten, IDs, Erfolge/Fehler).

## 6) Kurz‑Hilfe
- Cookies können ablaufen; bei Fehlern die beiden Werte einfach neu aus dem Browser übernehmen.
- 400/403 oder „passiert nichts“: `.env` prüfen und Cookies erneuern.  
- Viele Meldungen/Warnungen sind normal, solange der Fortschritt sichtbar weiterläuft.

## Sicherheit
- Nutzung auf eigenes Risiko.
- Cookies unbedingt vertraulich behandeln.
