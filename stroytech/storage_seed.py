"""SQLite schema creation and idempotent seed initialization."""
import json
from .storage_codec import _dump
from .storage_migration import _upgrade_seed
from .validation import validate_rule, semantic_key

def initialize_database(db, data_directory):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS equipment (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS rules (id TEXT PRIMARY KEY, payload TEXT NOT NULL, semantic_key TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, source_text TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('pending','conflict','approved','rejected')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_json TEXT NOT NULL, results_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
    ''')
    db.execute('BEGIN IMMEDIATE')
    equipment=json.loads((data_directory/'equipment.json').read_text(encoding='utf-8'))
    rules=[validate_rule(r) for r in json.loads((data_directory/'rules.json').read_text(encoding='utf-8'))]
    if db.execute("SELECT 1 FROM metadata WHERE key='seeded'").fetchone():
        _upgrade_seed(db,equipment,rules)
        return
    for machine in equipment:
        db.execute('INSERT INTO equipment VALUES (?,?)',(machine['id'],_dump(machine)))
    for rule in rules:
        db.execute('INSERT INTO rules VALUES (?,?,?)',(rule['id'],_dump(rule),semantic_key(rule)))
    db.execute("INSERT INTO metadata VALUES ('seeded','1')")
    db.execute("INSERT INTO metadata VALUES ('seed_version','2')")
