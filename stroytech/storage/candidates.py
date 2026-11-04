"""Candidate staging and listing without expert approval."""
import json
from stroytech.storage.codec import _candidate, _dump
from stroytech.validation import find_conflicts

def list_candidates(db):
    result=[]
    for row in db.execute('SELECT * FROM candidates ORDER BY id DESC'):
        item=json.loads(row['payload'])
        item['rule_id']=item['id']
        item['id']=row['id']
        item['status']=row['status']
        item['source_text']=row['source_text']
        result.append(item)
    return result


def add_candidates(db,candidates,source_text):
    if not isinstance(candidates,list) or not isinstance(source_text,str):
        raise ValueError('Нужен список кандидатов и исходный текст')
    normalized=[_candidate(c) for c in candidates]
    db.execute('BEGIN IMMEDIATE')
    approved=[json.loads(row[0]) for row in db.execute('SELECT payload FROM rules')]
    ids=[]
    for item in normalized:
        conflicts=find_conflicts(item,approved)
        status='conflict' if conflicts else 'pending'
        item['conflicts']=conflicts
        cursor=db.execute('INSERT INTO candidates(payload,source_text,status) VALUES (?,?,?)',(_dump(item),source_text,status))
        ids.append(cursor.lastrowid)
    return ids
