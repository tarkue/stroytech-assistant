"""Allowed fact fields and typed domain values."""
import math

CATEGORIES = {'work': {'excavation','drilling','lifting','transport','concrete'}, 'soil': {'firm','rock','soft','swamp'}, 'weather': {'dry','rain','slush'}, 'lift_purpose': {'cargo','people'}}
BOOLEANS = {'groundwater','near_powerline','obstacles','narrow_access','night','lighting','heavy','capacity_ok','access_risk'}
NUMBERS = {'duration_hours','load_t','radius_m','angle_deg'}
FIELDS = set(CATEGORIES) | BOOLEANS | NUMBERS | {'equipment_type'}



def number(value, positive=False):
    try:
        finite=isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    except OverflowError:
        finite=False
    if not finite or (value <= 0 if positive else value < 0):
        raise ValueError('Ожидалось конечное положительное число' if positive else 'Ожидалось конечное неотрицательное число')
    return value


def _value(field, value):
    if field in BOOLEANS:
        if type(value) is not bool:
            raise ValueError('Ожидалось логическое значение: '+field)
    elif field in NUMBERS:
        number(value, field == 'duration_hours')
        if field == 'angle_deg' and value > 90:
            raise ValueError('Угол должен быть от 0 до 90 градусов')
    elif field in CATEGORIES:
        if not isinstance(value,str) or value not in CATEGORIES[field]:
            raise ValueError('Недопустимое значение: '+field)
    elif not isinstance(value,str) or not value.strip():
        raise ValueError('Ожидалась непустая строка')
    return value
