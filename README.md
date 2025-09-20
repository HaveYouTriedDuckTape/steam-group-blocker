# Steam Group Members Blocker (Windows) [image:1]

Einfaches Windows‑Tool, das Mitglieder einer Steam‑Gruppe sammelt und anschließend blockiert oder entblockt, wobei alle Gruppen‑URLs ausschließlich aus der Datei groups.txt gelesen werden [image:1]

## Was wird benötigt [image:1]
- Windows 10/11 und Python 3.11 oder neuer, bei der Installation „Add Python to PATH“ aktivieren [image:1]
- Ein Steam‑Account, im Browser bereits angemeldet [image:1]

## Installation in 3 Schritten [image:1]
1) Projektordner vorbereiten und PowerShell im Ordner öffnen, dann ein virtuelles Environment anlegen und aktivieren [image:1]
   ```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ``` 
2) Benötigte Pakete installieren [image:1]
   ```
   pip install requests python-dotenv rich
   ``` 
3) groups.txt anlegen: Eine Gruppen‑URL pro Zeile, z. B [image:1]
   ```
   https://steamcommunity.com/groups/deine-gruppe-1
   https://steamcommunity.com/groups/deine-gruppe-2
   ```

## Cookies (.env) erstellen – so findest du sie [image:1]
1) Im Browser bei der Steam‑Community angemeldet sein, dann Entwicklerwerkzeuge öffnen (Taste F12) und zu „Application/Storage → Cookies → steamcommunity.com“ wechseln [image:1]
2) Die Werte von „sessionid“ und „steamLoginSecure“ kopieren, wie im Bild mit roten Pfeilen markiert, nur die Zeichenfolge rechts ohne Anführungszeichen [image:1]
3) Im Projektordner eine Datei .env anlegen und beide Werte eintragen [image:1]
   ```
   SESSIONID=hier_deine_sessionid
   STEAMLOGINSECURE=hier_dein_steamLoginSecure
   ```

Hinweis zum Bild: Es zeigt exakt die beiden benötigten Cookie‑Einträge „sessionid“ und „steamLoginSecure“ im Cookie‑Speicher des Browsers, die in die .env übernommen werden müssen [image:1]
![Uploading 68747470733a2f2f692e696d6775722e636f6d2f3238636b5852622e706e67.png…]()

## Skript starten [image:1]
- PowerShell im Projektordner öffnen, virtuelles Environment aktivieren und das Skript starten [image:1]
  ```
  .\.venv\Scripts\Activate.ps1
  python .\steam-group-blocker.py
  ```
- Während der Ausführung erscheint ein kompakter Fortschrittsbalken, der Seitenfortschritt, gesammelte IDs sowie Erfolge und Fehler anzeigt [image:1]

## Tipps bei Problemen (kurz) [image:1]
- Bei 400/403 Fehlern Cookies in .env erneuern, also „sessionid“ und „steamLoginSecure“ erneut aus dem Browser kopieren und speichern, dann Skript neu starten [image:1]
- Wenn die PowerShell das Aktivieren der virtuellen Umgebung blockiert, PowerShell als Administrator öffnen und „Set‑ExecutionPolicy RemoteSigned“ ausführen, dann erneut aktivieren [image:1]
- Bei auffällig vielen Verbindungswarnungen oder Aussetzern die parallele Last im Skript reduzieren und erneut probieren, das verbessert die Stabilität auf Windows oft deutlich [image:1]

## Sicherheit [image:1]
- Die Datei .env niemals weitergeben oder ins Internet hochladen, da sie Zugangsdaten enthält, und am besten in .gitignore eintragen, wenn ein Git‑Repository verwendet wird [image:1]
