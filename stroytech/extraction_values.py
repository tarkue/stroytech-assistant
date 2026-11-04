"""Bounded JSON decoding and typed neural values."""
import json
import math
from .extraction_schema import ExtractionError, FIELDS, MAX_RESPONSE

def _number(value):
    try:
        return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    except OverflowError:
        return False


def _value(field, value):
    if not isinstance(field,str) or field not in FIELDS:
        raise ExtractionError('Неизвестное поле: '+str(field))
    expected = FIELDS[field]
    valid = ((isinstance(expected,tuple) and value in expected)
             or (expected is bool and isinstance(value,bool))
             or (expected is float and _number(value) and value >= 0)
             or (expected is None and isinstance(value,str) and 0 < len(value) <= 200))
    if not valid or (field == 'duration_hours' and value == 0):
        raise ExtractionError('Неверное значение поля '+field)


def _object(raw):
    if not isinstance(raw,str) or len(raw)>MAX_RESPONSE:
        raise ExtractionError('Ответ модели слишком большой или не является текстом')
    try:
        result=json.loads(raw)
    except (ValueError, TypeError, RecursionError) as exc:
        raise ExtractionError('Модель вернула некорректный JSON') from exc
    if not isinstance(result,dict):
        raise ExtractionError('Ожидался JSON-объект')
    return result
