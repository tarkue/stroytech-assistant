"""Safe JSON serialization and candidate normalization."""
import json
from stroytech.validation import validate_rule

def _dump(value):
    try:
        return json.dumps(value,ensure_ascii=False,allow_nan=False)
    except (ValueError,TypeError) as exc:
        raise ValueError('Данные должны быть безопасным JSON') from exc


def _candidate(candidate):
    rule=validate_rule(candidate)
    entities=candidate.get('entities',[])
    if not isinstance(entities,list) or any(not isinstance(e,dict) or not isinstance(e.get('text'),str) or not isinstance(e.get('type'),str) for e in entities):
        raise ValueError('Некорректные сущности')
    for key in ('intent','evidence'):
        if not isinstance(candidate.get(key,''),str):
            raise ValueError('Некорректное поле '+key)
    return dict(rule,entities=entities,intent=candidate.get('intent',''),evidence=candidate.get('evidence',''),status='pending')
