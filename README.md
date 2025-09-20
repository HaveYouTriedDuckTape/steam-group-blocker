# Steam Group Members Blocker (Windows)

Dieses Tool liest Mitglieder einer Steam‑Gruppe ein und blockiert oder entblockt sie automatisiert. Diese Anleitung ist extra kurz und nur für Windows.

Wichtig
- Nutzung auf eigenes Risiko. Cookies privat halten.
- Es werden nur Gruppen‑URLs aus der Datei groups.txt verwendet.

---

## 1) Herunterladen und Ordner öffnen
- Den Projektordner z. B. nach C:\Users\<Name>\Documents\steam-group-blocker kopieren.
- PowerShell im Projektordner öffnen:
  - Rechtsklick im Ordner → „Im Terminal öffnen“.

## 2) Python und Umgebung
- Python 3.11 oder neuer installieren: https://www.python.org/downloads/windows/
- Benötigte Pakete installieren:
  ```
  pip install -r requirements.txt
  ```
  Falls keine requirements.txt vorhanden ist:
  ```
  pip install requests python-dotenv rich
  ```

## 3) Cookies eintragen (.env)
- Im Projektordner eine Datei .env anlegen.
- Zwei Werte aus dem eingeloggten Browser kopieren (Domain steamcommunity.com):
  - sessionid
  - steamLoginSecure
- Inhalt der .env:
  ```
  SESSIONID=hier_den_sessionid_wert_einfügen
  STEAMLOGINSECURE=hier_den_steamLoginSecure_wert_einfügen
  ```
- Tipp: Cookies im Browser finden (eingeloggt sein), dann Entwickler‑Werkzeuge öffnen → Speicher/Storage → Cookies → steamcommunity.com → sessionid und steamLoginSecure ablesen (siehe Screenshot).

## 4) Gruppenliste anlegen (groups.txt)
- Datei groups.txt im Projektordner erstellen.
- Pro Zeile genau eine Gruppen‑URL eintragen, z. B.:
  ```
  https://steamcommunity.com/groups/afd-esport
  ```
- Mehrere Gruppen sind möglich: einfach weitere Zeilen hinzufügen.

## 5) Starten
- Standard‑Start (liest groups.txt, verwendet .env):
  ```
  python .\main.py
  ```
- Während der Laufzeit:
  - Es erscheint ein kompakter Fortschrittsbalken (Seiten, IDs, OK/Fehler).
  - Bei Netzwerkfehlern wartet das Tool kurz und läuft automatisch weiter.

## 6) Häufige Fragen (kurz)
- „Dry‑Run“ (nur IDs anzeigen, nichts blocken)?
  - In der mitgelieferten Konfiguration kann ein Trockentest aktiviert sein; für einen echten Lauf sicherstellen, dass dieser aus ist.
- „Zu viele Meldungen in der Konsole“?
  - Normal. Die Anzeige bleibt bewusst kompakt; Warnungen sind unkritisch, wenn der Fortschritt weiterläuft.
- „Es passiert nichts“?
  - Prüfen, ob .env korrekt gefüllt ist und groups.txt gültige URLs enthält.
  - Bei weiterem Problem PowerShell neu starten und erneut versuchen.

## 7) Sicher aufräumen
- Beenden: Fenster schließen oder Strg + C.
- Virtuelle Umgebung beenden:
  ```
  deactivate
  ```
- .env niemals veröffentlichen.
