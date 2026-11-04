"""Versioned seed migration preserving expert knowledge and user prices."""
import json
from stroytech.storage.codec import _dump
from stroytech.validation import semantic_key

def _upgrade_seed(db,equipment,rules):
    """Upgrade only known seed fields; retain user prices and expert knowledge."""
    version=db.execute("SELECT value FROM metadata WHERE key='seed_version'").fetchone()
    if version and version[0]=='2':
        return
    for machine in equipment:
        if 'lifting' not in machine['work']:
            continue
        row=db.execute('SELECT payload FROM equipment WHERE id=?',(machine['id'],)).fetchone()
        if row:
            existing=json.loads(row[0])
            if 'lift_purpose' not in existing:
                existing['lift_purpose']=machine['lift_purpose']
                db.execute('UPDATE equipment SET payload=? WHERE id=?',(_dump(existing),machine['id']))
        elif machine['id']=='aerial-platform':
            db.execute('INSERT INTO equipment VALUES (?,?)',(machine['id'],_dump(machine)))
    for rule in rules:
        if rule['id'] not in {'r04','r05','r06','r23'}:
            continue
        row=db.execute('SELECT payload FROM rules WHERE id=?',(rule['id'],)).fetchone()
        if row and not json.loads(row[0]).get('source','').startswith('Учебная БЗ: вариант 2025_Б16'):
            continue
        duplicate=db.execute('SELECT id FROM rules WHERE semantic_key=? AND id<>?',(semantic_key(rule),rule['id'])).fetchone()
        if duplicate:
            # The expert's equivalent rule already supplies this knowledge.
            if row:
                db.execute('DELETE FROM rules WHERE id=?',(rule['id'],))
            continue
        db.execute('INSERT INTO rules VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, semantic_key=excluded.semantic_key',(rule['id'],_dump(rule),semantic_key(rule)))
    db.execute("INSERT INTO metadata VALUES ('seed_version','2') ON CONFLICT(key) DO UPDATE SET value=excluded.value")
