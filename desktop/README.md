# Desktop-Entwicklung

Stand: 14.09.2026. Der Windows-Prototyp, Benutzerverwaltung und vollständige ZIP-Sicherung/Wiederherstellung sind implementiert. Es gibt noch keinen freigegebenen Installer.

## Aus dem Quellcode starten (Entwicklung)

Das Repository muss für den nativen Windows-Test auf einem lokalen Windows-Laufwerk liegen, z. B. `C:\dev\education-center-crm`. Das Laden der .NET-Bibliothek von einem WSL-UNC-Pfad scheiterte im Test; derselbe Test aus einem lokalen Windows-Verzeichnis war erfolgreich.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt
.venv\Scripts\pythonw.exe -m desktop
```

Windows benötigt WebView2. Die spätere Installation soll Python mitliefern und die WebView2-Voraussetzung prüfen. Die obigen Befehle sind Entwicklerbefehle, kein Installationsablauf für Kunden.

Für getrennte Testdaten:

```powershell
.venv\Scripts\python.exe -m desktop --data-dir C:\temp\crm-test-data
```

## Daten und Lebenszyklus

- Standard unter Windows: `%LOCALAPPDATA%\EducationCenterCRM`.
- `crm.db`: lokale SQLite-Daten; `uploads/avatars`: Profilbilder; `session.key`: individueller Sitzungsschlüssel; `logs`: begrenzte Protokolle; `backups`: Sicherungen vor Schema-Migrationen.
- Der Betriebssystem-Lock verhindert zwei Desktop-Prozesse für denselben Datenordner. Nach Prozessende wird er freigegeben; `app.lock` darf bestehen bleiben.
- Waitress bindet ausschließlich an `127.0.0.1` mit einem freien Port. Ein zufälliger Zugang pro Start schützt die lokale HTTP-Oberfläche zusätzlich zu Anmeldung und CSRF. Die native Fensteroberfläche öffnet diesen Zugang automatisch.
- Fenster schließen beendet den lokalen Dienst. Es wird kein externer Server benötigt.
- Ein neuer Desktop-Datenordner enthält keine Demo-Konten oder Beispieldatensätze. Die erste Einrichtung erstellt Zentrum und Admin atomar. Danach ist `/setup` geschlossen, auch wenn später Konten gelöscht werden.
- Schema 1 und 2 werden mit vorherigem SQLite-Backup auf Schema 3 erweitert. Unbekannte Versionen und beschädigte Datenbanken werden nicht durch eine neue Datenbank ersetzt.
- Bestehende Web-Demodaten werden nicht automatisch in die Desktop-Daten kopiert.

Der Web-Entwicklungseinstieg `app/main.py` bleibt standardmäßig im Demo-Modus. Für einen leeren Web-Test müssen `CRM_DEMO_MODE=0`, ein eigener `CRM_DB_PATH` und `CRM_SECRET_KEY` gesetzt sein. Der Desktop verwendet direkt die App-Factory und erzwingt `DEMO_MODE=False`.

## Prüfungen

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.venv\Scripts\python.exe -m tools.run_tests
.venv\Scripts\python.exe -m tools.desktop_smoke
```

`tools.run_tests` verwendet temporäre Datenbanken. Der native Smoke-Test öffnet ein eigenes temporäres Fenster, prüft den geladenen Einrichtungsbildschirm und beendet ihn automatisch. Er ersetzt keine visuelle Prüfung und keine Prüfung der nativen Datei-Dialoge.

## Konten und Sicherungen

Im Admin-Kontomenü stehen `Benutzerkonten` und `Datensicherung` zur Verfügung. Neue Konten müssen ihr Startpasswort ändern. Rollenänderungen, Deaktivierungen und Passwort-Resets machen bestehende Sitzungen ungültig. Lehrkraftkonten brauchen eine eindeutige aktive Lehrkraft-Zuordnung. Das eigene Admin-Konto und der letzte aktive Admin sind vor versehentlichem Entzug geschützt.

Ein Admin kann nach Passwortbestätigung einen einmaligen Wiederherstellungscode erzeugen. Der Code wird nur einmal angezeigt; in der Datenbank liegt ausschließlich ein Hash. Ohne vorher gesicherten Code oder einen weiteren aktiven Admin gibt es keinen allgemeinen Login-Bypass.

ZIP-Sicherungen enthalten eine SQLite-Snapshot-Datei, alle referenzierten Profilbilder und ein Prüfsummenmanifest. Die Dateien sind nicht verschlüsselt. Nach Upload erfolgt eine Vorschau; erst eine getrennte Bestätigung mit aktuellem Admin-Passwort aktiviert die Wiederherstellung. Limits: 128 MB und maximal 5000 Nutzdateien. Ungültige Pfade, Prüfsummen, Datenbanken oder fehlende Profilbilder werden abgewiesen.

Für eine Wiederherstellung wird ein unabhängiger Ordner unter `generations/` aufgebaut. Erst nach Prüfung und automatischer Sicherung des bisherigen Zustands wird `current.json` atomar auf diesen Ordner umgestellt. Alte Datenordner bleiben erhalten. `app_config()` liest bei jedem Start diesen Zeiger; DB und Bilder gehören so immer zum selben wiederhergestellten Stand. Ein neuer Sitzungsschlüssel und eine Datenstand-Kennung verhindern die Weiterverwendung alter Anmeldungen. Requests des lokalen Desktop-Dienstes werden während Schreib-/Sicherungsvorgängen serialisiert. Externe Programme dürfen die laufende Datenbank nicht parallel bearbeiten.

## Windows-Build für Entwicklung

Aus einer lokalen Windows-Kopie:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.venv\Scripts\python.exe -m PyInstaller --noconfirm education_crm.spec
```

Das Ergebnis unter `dist/EducationCenterCRM/` enthält Python und die Anwendung. Der gesamte Ordner ist nötig; die EXE allein genügt nicht. Nutzerdaten werden nicht in den Build aufgenommen. Der Build ist noch kein signierter Installer. Der versteckte Parameter `--smoke-test` führt im gepackten Programm den temporären nativen Rauchtest aus.

Georgische Anleitung zur bereitgestellten Testversion: [USER_TEST_GE.md](USER_TEST_GE.md).

## Noch vor einer Kundenfreigabe

1. Visuelle Windows-Abnahme: Skalierung, Tastatur, Fokus, Profilbild-Upload, CSV-Download und wiederholtes Öffnen/Schließen.
2. Installer, WebView2-Prüfung, Upgrade/Uninstall mit Erhalt der Nutzerdaten, Test auf einem frischen Windows-Profil.
3. Erst danach GitHub Release. Gemeinsame Daten auf mehreren Rechnern und mobile Apps bleiben separate Ausbaustufen.

Das ältere Datenbank-CLI sichert nur SQLite; es ist nicht die vollständige Desktop-Sicherung. Eine CLI-Wiederherstellung darf nur bei gestoppter App erfolgen und muss auf den tatsächlich aktiven Datenpfad zeigen.

## Konto löschen und ohne Sicherung neu beginnen

Unter `Benutzerkonten` führt `Konto endgültig löschen` auf eine eigene Bestätigungsseite. Die Ziel-E-Mail-Adresse und das aktuelle Passwort des ausführenden Admins sind erforderlich. Das angemeldete Konto und der letzte aktive Admin können nicht gelöscht werden. Zum Austausch eines Admins zuerst einen zweiten Admin erstellen und mit diesem anmelden. Verknüpfte Lehrkräfte und Unterrichtsdaten bleiben erhalten; vorhandene Sicherungen und Bilddateien werden bei dieser einzelnen Kontolöschung nicht bereinigt.

`Anwendung zurücksetzen` im Admin-Menü ist ausschließlich im Desktop verfügbar. Nach Eingabe von `ALLES LÖSCHEN` und des aktuellen Admin-Passworts wird ein dauerhafter Auftrag `reset-pending.json` geschrieben. Ab dann sind alle weiteren Anwendungsanfragen gesperrt. Die App vollständig schließen und über dieselbe Verknüpfung erneut öffnen. Beim Start, unter der Instanzsperre und vor Datenbank-/Logger-Initialisierung, werden die bekannten CRM-Daten einschließlich lokaler Backups, alter Wiederherstellungsgenerationen und Sitzungsschlüssel gelöscht. Es entsteht keine automatische Sicherung. Externe Exporte und fremde Dateien werden nicht gelöscht. Die Programmdateien bleiben erhalten.

Schlägt eine Löschung fehl, bleibt der Auftrag bestehen und der Start bricht ab. Beim nächsten Start wird die Bereinigung wiederholt; eine teilweise geleerte Datenbank wird nicht geöffnet. Erst nach erfolgreicher Bereinigung beginnt die Ersteinrichtung mit neuem Sitzungsschlüssel.

## Portable Windows delivery (supersedes AppData layout)

The frozen executable always defaults to `<executable parent>/../data`. Both `Start.cmd` and direct EXE launch use that same directory, independent of user name, drive letter and current working directory. Explicit `--data-dir` remains for isolated tests/support; source-mode defaults remain per-user. `PORTABLE_ROOT` is enabled only for the packaged default data location.

The main backup button in portable mode produces `data/backups/crm-portable-*.zip` with `application/`, a consistent SQLite snapshot plus referenced avatars in `data/`, a fresh session key, relative `Start.cmd`, instructions and checksums. Old backups, inactive restore generations, locks and logs are excluded. Restore the complete program by extracting into a new empty folder; do not overwrite a running installation. Data-only ZIP export and in-app validated restore remain available separately. The current data snapshot limit is 128 MB; full archive source limit is 2 GB / 20000 files. Full reset still clears data only and leaves application/ intact. Copy the entire closed application folder when moving machines.
