"""Strict candidate parsing before expert review."""
from stroytech.extraction.schema import ExtractionError, FIELDS
from stroytech.extraction.values import _object, _value, _number
from stroytech.validation import validate_rule

def _validate_rule(rule):
    if not isinstance(rule,dict):
        raise ExtractionError('Правило должно быть объектом')
    for key in ('id','title','source','intent','evidence'):
        if not isinstance(rule.get(key),str) or not rule[key].strip() or len(rule[key])>12000:
            raise ExtractionError('Отсутствует строка '+key)
    if rule.get('status') != 'pending':
        raise ExtractionError('Модель не может подтверждать правила')
    entities=rule.get('entities')
    if not isinstance(entities,list) or len(entities)>100:
        raise ExtractionError('Неверные сущности')
    for entity in entities:
        if not isinstance(entity,dict) or any(not isinstance(entity.get(k),str) or not entity[k] for k in ('text','type')):
            raise ExtractionError('Неверная сущность')
    conditions=rule.get('conditions')
    effects=rule.get('effects')
    if not isinstance(conditions,list) or not 1<=len(conditions)<=16 or not isinstance(effects,list) or not 1<=len(effects)<=16:
        raise ExtractionError('Требуются условия и следствия')
    for condition in conditions:
        if not isinstance(condition,dict) or condition.get('op') not in ('eq','ne','in','gt','gte','lt','lte'):
            raise ExtractionError('Неверный оператор')
        field=condition.get('field')
        value=condition.get('value')
        if condition['op']=='in':
            if not isinstance(value,list) or not value or len(value)>32:
                raise ExtractionError('Оператор in требует список')
            for member in value:
                _value(field,member)
        else:
            _value(field,value)
        if condition['op'] in ('gt','gte','lt','lte') and FIELDS[field] is not float:
            raise ExtractionError('Сравнение разрешено только для чисел')
    for effect in effects:
        if not isinstance(effect,dict):
            raise ExtractionError('Неверное следствие')
        kind=effect.get('kind')
        value=effect.get('value')
        if kind in ('reject','require','warn') and isinstance(value,str) and 0<len(value)<=1000:
            continue
        if kind=='surcharge' and _number(value) and value>=0:
            continue
        if kind=='fact' and isinstance(value,dict):
            _value(value.get('field'),value.get('value'))
            continue
        raise ExtractionError('Неверное следствие')


def parse_candidates(raw):
    """Strict JSON parsing; no eval, fenced-code repair, or silent dropping."""
    rules=_object(raw).get('rules')
    if not isinstance(rules,list) or len(rules)>12:
        raise ExtractionError('Ожидался список rules (не более 12)')
    for rule in rules:
        _validate_rule(rule)
        try:
            validate_rule(rule)
        except ValueError as exc:
            raise ExtractionError(str(exc)) from exc
    return rules
