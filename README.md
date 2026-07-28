# Education Center CRM

![Education Center CRM Dashboard](assets/dashboard-preview.png)

Eine deutschsprachige Flask- und SQLite-Anwendung für die tägliche Verwaltung
eines kleinen Bildungszentrums.

**Portfolio-Demo:** [Statische Vorschau öffnen](https://sandro-abashishvili.sandroabashishvili.chatgpt.site/demos/education-crm/)

Die Demo im Portfolio ist eine statische Vorschau, weil das Portfolio-Hosting
keinen dauerhaft laufenden Flask-/SQLite-Prozess bereitstellt. Dieses
GitHub-Repository enthält die funktionale Anwendung.

## Was das Projekt demonstriert

- sitzungsbasierte Administrator-Anmeldung
- Teilnehmerverwaltung mit Suche, Filtern, Profil, Bearbeitung und Status
- Kurse, Lehrkräfte, Gruppen und Gruppenzuordnung
- Unterrichtsplanung und Anwesenheit pro Teilnehmer
- Rechnungen, Teilzahlungen und automatisch aktualisierte Überfälligkeit
- aus der Datenbank berechnete Dashboard-Kennzahlen
- UTF-8-CSV-Exporte für Teilnehmer und Zahlungen
- responsive Desktop- und Mobile-Oberfläche
- getrennte Service-Schicht für Geschäftslogik
- automatisierte Regressionstests

## Lokal starten

```bash
git clone https://github.com/sandroabashishvili/education-center-crm.git
cd education-center-crm
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

Anschließend `http://127.0.0.1:5001/` öffnen.

Beim ersten Start wird die Datenbank automatisch angelegt und mit realistischen
Demodaten gefüllt.

### Demo-Anmeldung

```text
E-Mail:  admin@bildungszentrum.de
Passwort: admin123
```

Diese Zugangsdaten sind ausschließlich für die lokale Portfolio-Demo bestimmt.

## Tests

```bash
python -m unittest discover -s tests -v
```

Die Tests decken unter anderem Health- und Dashboard-Antworten,
Authentifizierungsschutz, Teilnehmer-CRUD, POST-only-Löschung,
Gruppenzuordnung, Anwesenheit, überfällige Zahlungen und CSV-Exporte ab.

## Konfiguration

Optionale Umgebungsvariablen:

```bash
export CRM_SECRET_KEY="replace-this-for-non-demo-use"
export CRM_DB_PATH="/absolute/path/to/crm.db"
export PORT="5001"
```

Siehe [.env.example](.env.example).

## Architektur

```text
.
├── app/
│   ├── main.py       # Flask-Start und Konfiguration
│   ├── database.py   # SQLite-Schema, Migrationen und Demodaten
│   ├── models.py     # Domain-Dataclasses
│   ├── routes.py     # HTTP-Routen und Request-Verarbeitung
│   ├── services.py   # Abfragen und Geschäftsregeln
│   ├── templates.py  # serverseitig gerenderte Oberfläche
│   └── utils.py      # Parsing-Helfer
├── assets/
├── docs/
├── tests/
└── requirements.txt
```

## Status und ehrliche Grenzen

Der aktuelle Stand ist ein abgeschlossener Portfolio-MVP für eine lokale
Demonstration. Er verwendet SQLite und erzeugte Beispieldaten und wird nicht als
fertiges Produktions-SaaS dargestellt.

Für einen Produktivbetrieb wären zusätzlich CSRF-Schutz, rollenbasierte
Berechtigungen, Passwort-Wiederherstellung, Audit-Logging,
Deployment-Konfiguration, geregelte Datenbankmigrationen, Backups und ein
Produktions-WSGI-Server erforderlich.

Weitere Details: [docs/current_status.md](docs/current_status.md).

## Autor

Aleksandre (Sandro) Abashishvili

[Portfolio](https://sandro-abashishvili.sandroabashishvili.chatgpt.site/) ·
[GitHub](https://github.com/sandroabashishvili) ·
[LinkedIn](https://www.linkedin.com/in/aleksandre-abashishvili-03417617a/)
