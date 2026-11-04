"""Transactional expert approval and rejection of staged rules."""
import json
from .storage_codec import _dump
from .validation import validate_rule, find_conflicts, semantic_key

def approve_candidate(db,id):
    if type(id) is not int:
        raise ValueError('Нужен целый ID кандидата')
    db.execute('BEGIN IMMEDIATE')
    row=db.execute('SELECT * FROM candidates WHERE id=?',(id,)).fetchone()
    if row is None or row['status'] not in ('pending','conflict'):
        raise ValueError('Кандидат недоступен для подтверждения')
    rule=validate_rule(json.loads(row['payload']))
    rules=[json.loads(r[0]) for r in db.execute('SELECT payload FROM rules')]
    if any(semantic_key(rule)==semantic_key(r) for r in rules):
        raise ValueError('Семантический дубликат правила')
    conflicts=find_conflicts(rule,rules)
    if conflicts:
        raise ValueError('Противоречие с правилами: '+', '.join(conflicts))
    # Model IDs are untrusted; assign a stable unique ID at expert confirmation.
    rule['id']='expert-'+str(id)
    db.execute('INSERT INTO rules VALUES (?,?,?)',(rule['id'],_dump(rule),semantic_key(rule)))
    db.execute("UPDATE candidates SET status='approved' WHERE id=?",(id,))
    return rule['id']


def reject_candidate(db,id):
    if type(id) is not int:
        raise ValueError('Нужен целый ID кандидата')
    cursor=db.execute("UPDATE candidates SET status='rejected' WHERE id=? AND status IN ('pending','conflict')",(id,))
    if cursor.rowcount!=1:
        raise ValueError('Кандидат недоступен для отклонения')
