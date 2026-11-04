"""Normalize and validate data-only production rules."""
from stroytech.validation.fields import FIELDS, NUMBERS, number, _value
from stroytech.validation.matching import _overlap

def validate_rule(rule):
    if not isinstance(rule,dict):
        raise ValueError('Правило должно быть объектом')
    out={}
    for key in ('id','title','source'):
        value=rule.get(key)
        if not isinstance(value,str) or not value.strip() or len(value)>10000:
            raise ValueError('Некорректное поле '+key)
        out[key]=value.strip()
    conditions=rule.get('conditions')
    effects=rule.get('effects')
    if not isinstance(conditions,list) or not conditions or len(conditions)>50:
        raise ValueError('Нужны условия правила')
    if not isinstance(effects,list) or not effects or len(effects)>50:
        raise ValueError('Нужны действия правила')
    out['conditions']=[]
    out['effects']=[]
    for c in conditions:
        if not isinstance(c,dict) or not isinstance(c.get('field'),str) or c['field'] not in FIELDS or not isinstance(c.get('op'),str) or c['op'] not in {'eq','ne','in','gt','gte','lt','lte'}:
            raise ValueError('Некорректное условие')
        field,op,value=c['field'],c['op'],c.get('value')
        if op in {'gt','gte','lt','lte'} and field not in NUMBERS:
            raise ValueError('Сравнение требует числового поля')
        if op=='in':
            if not isinstance(value,list) or not value:
                raise ValueError('in требует непустого списка')
            value=sorted(set(_value(field,v) for v in value))
        else:
            value=_value(field,value)
        out['conditions'].append(dict(field=field,op=op,value=value))
    for e in effects:
        if not isinstance(e,dict):
            raise ValueError('Некорректное действие')
        kind,value=e.get('kind'),e.get('value')
        if not isinstance(kind,str):
            raise ValueError('Некорректный вид действия')
        if kind in {'reject','require','warn'}:
            if not isinstance(value,str) or not value.strip():
                raise ValueError('Нужен текст действия')
        elif kind=='surcharge':
            number(value)
        elif kind=='fact':
            if not isinstance(value,dict) or not isinstance(value.get('field'),str) or value['field'] not in {'equipment_type','heavy','capacity_ok','access_risk'}:
                raise ValueError('Недопустимый выводимый факт')
            value={'field':value['field'],'value':_value(value['field'],value.get('value'))}
        else:
            raise ValueError('Неизвестное действие')
        out['effects'].append(dict(kind=kind,value=value))
    if not _overlap(out['conditions'],[]):
        raise ValueError('Условия правила несовместимы')
    assignments={}
    for e in out['effects']:
        if e['kind']=='fact':
            f,v=e['value']['field'],e['value']['value']
            if f in assignments and assignments[f]!=v:
                raise ValueError('Противоречивые действия')
            assignments[f]=v
    return out
