# Steam Group Members Blocker (Windows)

Einfaches Tool das Mitglieder einer Steam‑Gruppe sammelt und anschließend blockiert oder entblockt. 

Nutzung auf eigenes Risiko; Cookies unbedingt vertraulich behandeln.

---

## 1) Download & Ordner öffnen
- Auf GitHub den grünen „Code“-Button anklicken → „Download ZIP“ wählen.  
- ZIP entpacken (z. B. nach `C:\Users\<Name>\Documents\steam-group-blocker`) und den Ordner in PowerShell öffnen (Rechtsklick → „Im Terminal öffnen“).

## 2) Python vorbereiten
- Python 3.11 oder neuer installieren: https://www.python.org/downloads/windows/  
  Tipp: Beim Installer „Add Python to PATH“ anhaken.
- Abhängigkeiten installieren:
  ```
  pip install -r requirements.txt
  ```
  Falls `requirements.txt` fehlt:
  ```
  pip install requests python-dotenv rich
  ```

## 3) Cookies eintragen (.env)
- Im Projektordner eine Datei `.env` anlegen.  
- Im Browser bei steamcommunity.com eingeloggt sein, Entwickler‑Werkzeuge öffnen (F12) → „Application/Storage“ → „Cookies“ → `https://steamcommunity.com`.  
- Die Werte von `sessionid` und `steamLoginSecure` kopieren und in `.env` eintragen:
  ```
  SESSIONID=hier_den_sessionid_wert_einfügen
  STEAMLOGINSECURE=hier_den_steamLoginSecure_wert_einfügen
  ```
Hinweis: Cookies laufen ab – bei Fehlern später einfach die beiden Werte neu aus dem Browser kopieren.

## 4) Gruppenliste anlegen (groups.txt)
- Im Projektordner eine Datei `groups.txt` erstellen.  
- Pro Zeile genau eine Gruppen‑URL eintragen, z. B.:
  ```
  https://steamcommunity.com/groups/afd-esport
  ```
- Für mehrere Gruppen einfach weitere Zeilen hinzufügen.

## 5) Starten
- PowerShell im Ordner, ggf. venv re‑aktivieren:
  ```
  .\.venv\Scripts\Activate.ps1
  python .\steam-group-blocker.py
  ```
- Während der Ausführung zeigt das Tool einen kompakten Fortschrittsbalken (Seiten, IDs, Erfolge/Fehler).

## 6) Kurz‑Hilfe (häufige Fälle)
- Es passiert nichts oder Fehler 400/403: `.env` prüfen, Cookies ggf. erneuern.  
- PowerShell blockiert das Aktivieren der Umgebung: PowerShell als Admin starten und einmalig ausführen:
  ```
  Set-ExecutionPolicy RemoteSigned
  ```
- Zu viele Meldungen: Normal; so lange der Fortschritt läuft, ist keine Aktion nötig.
