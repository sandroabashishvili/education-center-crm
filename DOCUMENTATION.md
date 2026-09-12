# Education Center CRM – Dokumentation

## 1. Zweck

Education Center CRM ist eine serverseitig gerenderte Flask-Anwendung für kleine Bildungszentren. Der Fokus liegt auf einem nachvollziehbaren administrativen Ablauf: Personen verwalten, Kurse und Gruppen strukturieren, Unterricht planen, Anwesenheit erfassen und Zahlungen verfolgen.

Die Anwendung verwendet SQLite als lokale Datenbank und Jinja für die Oberfläche. Die öffentliche GitHub-Pages-Version unter `docs/` ist eine statische Portfolio-Vorschau und ersetzt nicht die echte Flask-Anwendung.

## 2. Hauptbereiche

### Dashboard

Das Dashboard bündelt zentrale Kennzahlen und operative Übersichten. Dazu gehören aktive Schüler, Kurse, Gruppen, Lehrkräfte, Unterrichtstermine, überfällige Rechnungen, Einnahmen und Anwesenheitswerte.

Es dient als Einstiegspunkt und verweist auf die wichtigsten Arbeitsbereiche.

### Schüler

Der Bereich `Schüler` unterstützt:

- Suche nach Name, E-Mail, Telefon und Kontaktperson
- Statusfilter
- Detailansicht
- Bearbeitung
- Löschung durch berechtigte Rollen
- Gruppenzuordnungen
- Zahlungsübersicht im Schülerprofil
- CSV-Export

### Lehrkräfte

Der Bereich `Lehrkräfte` unterstützt:

- Suche nach Name, E-Mail, Telefon und Fachgebiet
- Statusfilter
- Detailansicht
- Bearbeitung
- Gruppenzuordnungen
- Löschung durch Administratoren

Wenn eine Lehrkraft gelöscht wird, bleiben zugehörige Gruppen bestehen; die Zuordnung wird entfernt.

### Kurse

Der Bereich `Kurse` unterstützt:

- Suche nach Kursname, Kategorie und Beschreibung
- Statusfilter
- Detailansicht
- Bearbeitung
- Standardgebühr
- Anzeige zugehöriger Gruppen
- Löschung durch Administratoren

### Gruppen

Der Bereich `Gruppen` verbindet Kurse, Lehrkräfte und Schüler.

Unterstützt werden:

- Suche nach Gruppenname, Kurs, Lehrkraft und Zeitplan
- Statusfilter
- Kapazität
- Start- und Enddatum
- Zeitplanbeschreibung
- Detailansicht
- Bearbeitung
- Teilnehmerzuordnung
- Löschung durch Administratoren

Beim Löschen einer Gruppe werden zugehörige Unterrichtstermine, Anwesenheitsdaten und Gruppenzuordnungen entfernt. Rechnungen bleiben erhalten; ihre Gruppenreferenz wird gelöst.

### Unterricht

Der Bereich `Unterricht` unterstützt:

- Suche nach Gruppe, Lehrkraft, Raum und Thema
- Statusfilter
- Planung von Unterrichtsterminen
- Beginn und Ende
- Raum
- Thema
- Anwesenheitserfassung

Lehrkräfte sehen ausschließlich Ressourcen, die ihrer Rolle und Zuordnung entsprechen.

### Zahlungen

Der Bereich `Zahlungen` unterstützt:

- Suche nach Schüler, Gruppe, Zahlungsart und Notiz
- Statusfilter
- Rechnungserstellung
- Detailansicht
- Bearbeitung
- Löschung durch Administratoren
- Erfassung von Teilzahlungen
- automatische Berechnung von Zahlungsstatus
- CSV-Export

Verwendete Statuswerte sind unter anderem `paid`, `partial`, `pending` und `overdue`.

Eine Zahlung kann nicht über den noch offenen Betrag hinaus erfasst werden. Bereits bezahlte Beträge bleiben beim Bearbeiten einer Rechnung erhalten.

## 3. Rollenmodell

### Administrator

Der Administrator besitzt den umfassendsten Zugriff und darf geschützte Datensätze löschen.

### Mitarbeiter / Manager

Manager können die tägliche Verwaltung durchführen, jedoch nicht alle administrativen Löschaktionen ausführen.

### Lehrkraft

Lehrkräfte haben einen begrenzten operativen Zugriff auf eigene Gruppen, Unterrichtstermine und Anwesenheitsfunktionen.

## 4. Navigation

Die Navigation ist nach Arbeitslogik aufgebaut:

```text
Dashboard
→ Schüler
→ Lehrkräfte
→ Kurse
→ Gruppen
→ Unterricht
→ Zahlungen
```

Die Reihenfolge geht von Personen über Bildungsstruktur und operative Arbeit bis zu Finanzen.

## 5. UI-Konventionen

Verwaltungslisten verwenden eine einheitliche Aktionssprache:

- `Öffnen` – neutrale Outline-Aktion
- `Bearbeiten` – primäre Bearbeitungsaktion
- `Löschen` – rote Gefahrenaktion

Die wichtigsten Listen verwenden eine gemeinsame Filterleiste mit Suchfeld, Statusfilter, Zurücksetzen-Funktion und Trefferzähler.

## 6. Responsive Design

Die Oberfläche verwendet mehrere responsive Stufen. Wichtige Bereiche werden schrittweise angepasst:

- Hauptnavigation wechselt auf ein einklappbares mobiles Menü
- Filterleisten werden von mehreren Spalten auf eine Spalte reduziert
- Detail-Metadaten wechseln von vier auf zwei und anschließend eine Spalte
- Aktionsbuttons werden mobil untereinander angeordnet
- Tabellen werden als mobile Karten dargestellt
- Modale Dialoge erhalten volle Breite und interne Scrollbarkeit
- Dashboard-Karten reduzieren ihre Spaltenzahl

Zusätzlich wird mit stabilem Scrollbar-Gutter verhindert, dass sich das gesamte Layout beim Seitenwechsel seitlich verschiebt.

## 7. Profil und Konto

Angemeldete Benutzer besitzen ein Account-Menü im Header. Dort werden Name, Rolle und Avatar dargestellt.

Die Profilseite unterstützt Kontodaten, Avatarverwaltung und Passwortänderung. Uploads sind größenbeschränkt und werden unter `app/static/uploads/avatars/` gespeichert.

## 8. Sicherheit

Die Anwendung verwendet unter anderem:

- Passwort-Hashing über Werkzeug
- CSRF-Schutz über Flask-WTF
- rollenbasierte Zugriffskontrolle
- serverseitige Validierung
- `HttpOnly` Session-Cookies
- `SameSite=Lax`
- begrenzte Uploadgröße

Die voreingestellte lokale Secret-Key-Konfiguration ist nur für Entwicklung und Demo gedacht. Für produktiven Betrieb muss `CRM_SECRET_KEY` extern gesetzt werden.

## 9. Datenbank

Standardmäßig wird SQLite verwendet.

Der Pfad kann über folgende Umgebungsvariable geändert werden:

```bash
export CRM_DB_PATH="/absolute/path/to/crm.db"
```

Beim Start initialisiert die Anwendung das Schema über `database.init_db()`.

## 10. Backup und Restore

```bash
python3 -m tools.database_cli backup
python3 -m tools.database_cli restore --from app/backups/education-crm-DATUM.db --confirm
```

Das Restore-Werkzeug erstellt vor dem Überschreiben eine zusätzliche Sicherung und prüft die SQLite-Datenbank.

## 11. Tests

Alle Tests können mit folgendem Befehl ausgeführt werden:

```bash
python3 -m unittest discover -s tests -v
```

Die Tests prüfen unter anderem:

- Authentifizierung
- Rollenrechte
- CSRF-Schutz
- Schülerfunktionen
- Profilfunktionen
- Kursmanagement
- Lehrkräftemanagement
- Gruppenmanagement
- Zahlungsmanagement
- Anwesenheit
- Validierung
- CSV-Export
- Datenbankwerkzeuge

## 12. GitHub-Pages-Demo

Die öffentliche Demo wird aus `docs/` bereitgestellt.

Sie bildet die aktuelle visuelle Struktur des echten CRM nach:

- gleiche Navigationsreihenfolge
- Dashboard
- Schüler
- Lehrkräfte
- Kurse
- Gruppen
- Unterricht
- Zahlungen
- einheitliche Aktionsbuttons
- Such- und Statusfilter
- mobile Navigation
- responsive Tabellen

Da GitHub Pages keine Flask-Anwendung und keine SQLite-Datenbank ausführt, sind schreibende Aktionen in der Demo deaktiviert. Navigation, Suche und Filter funktionieren rein clientseitig.

## 13. Architektur

```text
Browser
  ↓
Flask routes
  ↓
Services / Business Rules
  ↓
SQLite
```

Wichtige Dateien:

```text
app/main.py
app/routes.py
app/management_routes.py
app/profile_routes.py
app/services.py
app/database.py
app/models.py
app/utils.py
app/templates/
app/static/
tests/
tools/
docs/
```

Die Trennung zwischen Kernrouten, Management-Routen und Profil-Routen hält die Codebasis übersichtlicher als eine einzelne große Routendatei.

## 14. Entwicklungsstatus

Das Projekt ist ein funktionsfähiges Portfolio-CRM und wird aktiv weiterentwickelt.

Für einen externen Produktivbetrieb wären zusätzlich sinnvoll:

- produktiver WSGI-Server
- Reverse Proxy
- HTTPS-Konfiguration
- Audit-Logging
- Passwort-Wiederherstellung
- erweiterte Benutzerverwaltung
- Monitoring und Fehlertracking
- Deployment-Pipeline
- Datenschutz- und Aufbewahrungskonzept
- serverseitige Pagination bei sehr großen Datenmengen

## 15. Autor

Sandro Abashishvili

- Portfolio: https://sandro-abashishvili.de/
- GitHub: https://github.com/sandroabashishvili
- LinkedIn: https://www.linkedin.com/in/aleksandre-abashishvili-03417617a/
