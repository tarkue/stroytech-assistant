"""Human-readable display of stored facts and production rules."""
from .ui_labels import CHOICES, LABELS, PURPOSE
from .ui_order_data import money

def display_value(field, value):
    """Translate presentation values without changing stored rule data."""
    if isinstance(value,list):
        return ', '.join(display_value(field,item) for item in value)
    if value is True: return 'да'
    if value is False: return 'нет'
    if value is None: return 'неизвестно'
    choices=CHOICES.get(field,{})
    if field=='lift_purpose': choices=PURPOSE
    known={stored:label.lower() for label,stored in choices.items()}
    equipment_names={'mini_excavator':'мини-экскаватор','tracked_excavator':'гусеничный экскаватор','wheeled_excavator':'колёсный экскаватор','compact_drill':'компактная буровая','heavy_drill':'тяжёлая буровая','crane':'автокран','manipulator':'манипулятор','truck':'грузовик','mixer':'бетономешалка','aerial_platform':'автовышка'}
    if field=='equipment_type': known=equipment_names
    return known.get(value,str(value))


def condition_text(condition):
    operators={'eq':'—','ne':'не','in':'— один из вариантов:','gt':'больше','gte':'не меньше','lt':'меньше','lte':'не больше'}
    field=condition['field']
    return f"{LABELS.get(field,field)} {operators.get(condition['op'],condition['op'])} {display_value(field,condition['value'])}"


def effect_text(effect):
    kind,value=effect['kind'],effect['value']
    if kind=='fact':
        return 'Установить: '+LABELS.get(value['field'],value['field'])+' — '+display_value(value['field'],value['value'])
    if kind=='surcharge': return 'Добавить к стоимости '+money(value)
    labels={'reject':'Исключить вариант','require':'Условие','warn':'Учесть'}
    return labels.get(kind,kind)+': '+str(value)


def render_rule(rule):
    import streamlit as st
    st.markdown('**Если**')
    for condition in rule['conditions']:
        st.write('• '+condition_text(condition))
    st.markdown('**То**')
    for effect in rule['effects']:
        st.write('• '+effect_text(effect))
