"""Order parsing, price formatting and local database location."""
import math
import os
from pathlib import Path
from stroytech.ui.labels import BOOL_FIELDS, CHOICES, LABELS, NUM_FIELDS, PURPOSE

def parse_order(values):
    """Translate display labels and enforce finite, positive dimensions."""
    order={field:CHOICES[field].get(values.get(field)) for field in CHOICES}
    order['lift_purpose']=PURPOSE.get(values.get('lift_purpose')) if order['work']=='lifting' else None
    order.update({field:{'Да':True,'Нет':False}.get(values.get(field)) for field in BOOL_FIELDS})
    for field in NUM_FIELDS:
        raw=values.get(field,'').strip().replace(',','.')
        if not raw and field!='duration_hours':
            order[field]=None
            continue
        try:
            value=float(raw)
        except ValueError:
            raise ValueError(f'{LABELS[field]}: введите число.') from None
        if not math.isfinite(value) or value<0 or (field!='angle_deg' and value==0) or (field=='angle_deg' and value>90):
            raise ValueError(f'{LABELS[field]}: длительность, масса и вылет должны быть больше нуля; угол — от 0 до 90°.')
        order[field]=value
    return order


def money(value):
    return f'{value:,.0f} ₽'.replace(',',' ') if value is not None else 'Не определена'


def database_path():
    default=Path(__file__).resolve().parents[2]/'data'/'app.sqlite3'
    return Path(os.environ.get('STROYTECH_DB',str(default))).expanduser().resolve()
