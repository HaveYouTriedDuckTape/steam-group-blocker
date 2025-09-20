# Steam Group Members Blocker

Einfaches Tool das automatisch alle Mitglieder der Steam-AfD-Gruppen bei Steam blockieren

## 1) Download & Ordner öffnen
- Auf GitHub den grünen „Code“-Button klicken → „Download ZIP“ wählen und das ZIP entpacken.  
- Im entpackten Ordner PowerShell öffnen

## 2) Python einrichten
- Python 3.11+ installieren: https://www.python.org/downloads/windows/ (Häkchen „Add Python to PATH“ setzen).  
- Abhängigkeiten installieren:
  ```
  py -m pip install -r requirements.txt
  ```
  Falls die Datei fehlt:
  ```
  py -m pip install --user requests python-dotenv rich
  ```

## 3) Cookies finden und kopieren
- Im Browser bei steamcommunity.com angemeldet sein
- Dann Entwicklerwerkzeuge (F12) → „Application/Storage“ → „Cookies“ → `https://steamcommunity.com`.

  <img width="765" height="345" alt="68747470733a2f2f692e696d6775722e636f6d2f3238636b5852622e706e67" src="https://github.com/user-attachments/assets/9c68e94a-0a08-411e-8ccb-1fb6d8608259" />

## 3a) Cookies eintragen, Version A: .env-Datei
- Im Projektordner eine Datei `.env` anlegen. (Einfache eine Textdatei anlegen und in ".env" umbenennen)
- Die Werte `sessionid` und `steamLoginSecure` in die .env-Datei kopieren und so eintragen:
  ```
  SESSIONID=hier_deine_sessionid
  STEAMLOGINSECURE=hier_dein_steamLoginSecure
  ```
## 3b) Cookies eintragen, Version B: config.toml
- Die Stelle in config.toml von:
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
  sessionid = "hier_deine_sessionid"
  steamLoginSecure = "hier_dein_steamLoginSecure"
  ```

## 4) Start
- PowerShell im Ordner:
  ```
  python .\steam-group-blocker.py
  ```

## 5) Kurz‑Hilfe
- Cookies können ablaufen; bei Fehlern die beiden Werte einfach neu aus dem Browser übernehmen.
- 400/403 oder „passiert nichts“: `.env` prüfen und Cookies erneuern.  
- Viele Meldungen/Warnungen sind normal, solange der Fortschritt sichtbar weiterläuft.

## Sicherheit
- Nutzung auf eigenes Risiko.
- Cookies unbedingt vertraulich behandeln.
- `.env` ggf. `config.toml` enthälten die Cookies-Daten und dürfen niemals geteilt oder veröffentlicht werden.

#### Hat jemand Kaffee für mich 🥹? 
<details>
  <summary><b>Unterstützen</b></summary>

  Wenn dir dieses Projekt gefällt, kannst du mich mit einem Kaffee unterstützen. Danke! 🫶

  [![Ko-fi](https://img.shields.io/badge/support_me_on_ko--fi-F16061?style=for-the-badge&logo=kofi&logoColor=f5f5f5)](https://ko-fi.com/haveyoutriedducktape)

</details>
