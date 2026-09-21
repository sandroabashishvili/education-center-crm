"""Run all tests without importing the demo entrypoint against a working database."""
import os
from pathlib import Path
import tempfile
import unittest


def main():
    previous = os.environ.get('CRM_DB_PATH')
    try:
        with tempfile.TemporaryDirectory(prefix='crm-tests-') as directory:
            os.environ['CRM_DB_PATH'] = str(Path(directory) / 'bootstrap.db')
            suite = unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parents[1] / 'tests'))
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            return int(not result.wasSuccessful())
    finally:
        if previous is None:
            os.environ.pop('CRM_DB_PATH', None)
        else:
            os.environ['CRM_DB_PATH'] = previous


if __name__ == '__main__':
    raise SystemExit(main())
