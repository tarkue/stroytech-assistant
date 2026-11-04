"""Public validation, conflicts, semantic keys and order checks."""
import json
from .rule_fields import CATEGORIES, BOOLEANS, NUMBERS, FIELDS, number, _value
from .rule_matching import matches, _overlap
from .rule_validation import validate_rule

def find_conflicts(rule,rules):
    rule=validate_rule(rule)
    conflicts=[]
    for other in rules:
        other=validate_rule(other)
        if not _overlap(rule['conditions'],other['conditions']):
            continue
        for a in rule['effects']:
            for b in other['effects']:
                if a['kind']==b['kind']=='fact' and a['value']['field']==b['value']['field'] and a['value']['value']!=b['value']['value']:
                    conflicts.append(other['id'])
                    break
    return sorted(set(conflicts))


def semantic_key(rule):
    rule=validate_rule(rule)
    for c in rule['conditions']:
        if c['op']=='in' and len(c['value'])==1:
            c['op']='eq'
            c['value']=c['value'][0]
        if c['field'] in NUMBERS:
            c['value']=[float(v) for v in c['value']] if c['op']=='in' else float(c['value'])
    canonical=lambda values: sorted(json.dumps(v,sort_keys=True,ensure_ascii=False) for v in values)
    return json.dumps([canonical(rule['conditions']),canonical(rule['effects'])],ensure_ascii=False)


def validate_order(order):
    if not isinstance(order,dict):
        raise ValueError('Заказ должен быть объектом')
    for field,value in order.items():
        if field not in FIELDS:
            raise ValueError('Неизвестное поле заказа: '+field)
        if field not in {'equipment_type','heavy','capacity_ok','access_risk'} and value is not None:
            _value(field,value)
            if field in {'load_t','radius_m'}:
                number(value,True)
    return {k:v for k,v in order.items() if k not in {'equipment_type','heavy','capacity_ok','access_risk'}}
