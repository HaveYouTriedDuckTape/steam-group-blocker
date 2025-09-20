# Steam Group Members Blocker

Dieses Tool liest Mitglieder einer Steam‑Gruppe ein und blockiert oder entblockt sie automatisiert.

---

## 1) Herunterladen Entpacken und Ordner öffnen
- Grüner Code-Button dürcken -> als Zip downloaden
- Den Projektordner aus dem zip entpacken

## 2) Python und Umgebung
- Python 3.11 oder neuer installieren: https://www.python.org/downloads/windows/
- PowerShell im Projektordner öffnen:
  - Rechtsklick im Ordner → „Im Terminal öffnen“.
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
  <img width="765" height="345" alt="68747470733a2f2f692e696d6775722e636f6d2f3238636b5852622e706e67" src="https://github.com/user-attachments/assets/c203dc64-f65a-4a90-918a-096ad90d66eb" />

 
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
  python .\steam-group-blocker.py
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


Nutzung auf eigenes Risiko. Cookies privat halten.
