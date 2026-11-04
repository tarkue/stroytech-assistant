"""SQLite repository facade preserving the public persistence interface."""
import json
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from .validation import validate_order, validate_rule, find_conflicts, semantic_key
from .storage_codec import _dump, _candidate
from .storage_migration import _upgrade_seed
from .storage_seed import initialize_database
from . import storage_candidates, storage_approval

DATA_DIRECTORY = Path(__file__).resolve().parents[1] / 'data'


class Repository:

    def __init__(self,path):
        self.path=str(path)

    @contextmanager
    def _connect(self):
        connection=sqlite3.connect(self.path,timeout=10)
        connection.row_factory=sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        """Create or upgrade schema and seeds without discarding user data."""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            initialize_database(db, DATA_DIRECTORY)

    def _list(self,table):
        with self._connect() as db:
            return [json.loads(row['payload']) for row in db.execute('SELECT payload FROM '+table+' ORDER BY id')]

    def list_equipment(self):
        return self._list('equipment')

    def list_rules(self):
        return self._list('rules')

    def list_candidates(self):
        with self._connect() as db:
            return storage_candidates.list_candidates(db)

    def add_candidates(self,candidates,source_text):
        with self._connect() as db:
            return storage_candidates.add_candidates(db,candidates,source_text)

    def approve_candidate(self,id):
        with self._connect() as db:
            return storage_approval.approve_candidate(db,id)

    def reject_candidate(self,id):
        with self._connect() as db:
            return storage_approval.reject_candidate(db,id)

    def save_order(self,order,results):
        validate_order(order)
        if not isinstance(results,list):
            raise ValueError('Нужен список результатов')
        with self._connect() as db:
            return db.execute('INSERT INTO orders(order_json,results_json) VALUES (?,?)',(_dump(order),_dump(results))).lastrowid
