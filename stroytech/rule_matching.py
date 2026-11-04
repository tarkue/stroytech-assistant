"""Known-fact matching and satisfiable condition overlap."""
import math
from .rule_fields import CATEGORIES, BOOLEANS, NUMBERS

def matches(condition, facts):
    field,op,v=condition['field'],condition['op'],condition['value']
    actual=facts.get(field)
    if actual is None:
        return False
    if op=='eq':
        return actual==v
    if op=='ne':
        return actual!=v
    if op=='in':
        return actual in v
    if op=='gt':
        return actual>v
    if op=='gte':
        return actual>=v
    if op=='lt':
        return actual<v
    return actual<=v


def _overlap(left,right):
    for field in {c['field'] for c in left+right}:
        conditions=[c for c in left+right if c['field']==field]
        if field in NUMBERS:
            bounds=[c['value'] for c in conditions if c['op']!='in']+[v for c in conditions if c['op']=='in' for v in c['value']]
            points=sorted(set([0]+bounds+([90] if field=='angle_deg' else [])))
            samples=points+[a+(b-a)/2 for a,b in zip(points,points[1:])]+[math.nextafter(max(points),math.inf)]
            samples=[x for x in samples if math.isfinite(x) and x >= 0 and (field not in {'duration_hours','load_t','radius_m'} or x>0) and (field!='angle_deg' or x<=90)]
            if not any(all(matches(c,{field:x}) for c in conditions) for x in samples):
                return False
        else:
            values=set(CATEGORIES.get(field, {True,False} if field in BOOLEANS else {'__other__'}))
            for c in conditions:
                values.update(c['value'] if c['op']=='in' else [c['value']])
            if not any(all(matches(c,{field:x}) for c in conditions) for x in values):
                return False
    return True
