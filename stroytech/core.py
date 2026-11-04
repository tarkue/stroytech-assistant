"""Data-driven forward chaining. All costs and capacity charts are educational."""
from .validation import validate_rule, find_conflicts, matches, validate_order, number

ENVIRONMENT = ('soil','weather','groundwater','near_powerline','obstacles','narrow_access','night')

def _capacity(order, machine):
    if order.get('work')!='lifting': return None
    if any(order.get(f) is None for f in ('load_t','radius_m','angle_deg')): return None
    chart=machine.get('capacity_table',[])
    # A chart entry covers no greater radius and no smaller boom angle.
    eligible=[row['capacity_t'] for row in chart if order['radius_m']<=row['radius_m'] and order['angle_deg']>=row['angle_deg']]
    if not eligible: return None
    return order['load_t']<=max(eligible)

def _infer(facts,rules):
    fired=set(); trace=[]; effects=[]; contradictory=False
    # Each rule fires at most once, so even cyclic fact rules terminate in N+1 passes.
    for _ in range(len(rules)+1):
        changed=False
        for rule in rules:
            if rule['id'] in fired or not all(matches(c,facts) for c in rule['conditions']): continue
            fired.add(rule['id']); changed=True
            entry={'rule_id':rule['id'],'title':rule['title'],'conditions':rule['conditions'],'effects':rule['effects'],'facts_before':dict(facts)}
            for effect in rule['effects']:
                if effect['kind']!='fact':
                    effects.append((rule['id'],effect)); continue
                field,value=effect['value']['field'],effect['value']['value']
                if facts.get(field) is not None and facts[field]!=value:
                    contradictory=True; entry['conflict']='Несовместимые значения факта '+field
                    continue
                facts[field]=value
            entry['facts_after']=dict(facts); trace.append(entry)
        if not changed: break
    return effects,trace,contradictory

def _equipment(machine):
    if not isinstance(machine,dict) or not all(k in machine for k in ('id','name','work','equipment_type','heavy','rate_per_hour','delivery_cost')): raise ValueError('Неполная карточка техники')
    if not isinstance(machine['work'],list) or type(machine['heavy']) is not bool: raise ValueError('Некорректная карточка техники')
    if 'lifting' in machine['work'] and machine.get('lift_purpose') not in ('cargo','people'): raise ValueError('Нужно назначение подъёмной техники: cargo/people')
    number(machine['rate_per_hour'],True); number(machine['delivery_cost'])
    for row in machine.get('capacity_table',[]):
        for key in ('radius_m','capacity_t'): number(row[key],True)
        number(row['angle_deg'])
        if row['angle_deg']>90: raise ValueError('Некорректный угол таблицы')
    return machine

def _recommend_one(order,machine,rules):
    facts=dict(order, equipment_type=machine['equipment_type'],heavy=machine['heavy'])
    facts['capacity_ok']=_capacity(order,machine)
    effects,trace,conflict=_infer(facts,rules)
    missing=[f for f in ('work','duration_hours')+ENVIRONMENT if order.get(f) is None]
    if order.get('night') is True and order.get('lighting') is None: missing.append('lighting')
    if order.get('work')=='lifting':
        if order.get('lift_purpose') is None: missing.append('lift_purpose')
        missing.extend(f for f in ('load_t','radius_m','angle_deg') if order.get(f) is None)
        if not any(f in missing for f in ('load_t','radius_m','angle_deg')) and facts['capacity_ok'] is None: missing.append('capacity_table')
    reasons=[e['value'] for _,e in effects if e['kind'] in {'reject','require','warn'}]
    rejected=any(e['kind']=='reject' for _,e in effects)
    conditional=any(e['kind'] in {'require','warn'} for _,e in effects)
    if conflict: reasons.append('Противоречие в выводимых фактах: требуется проверка эксперта')
    status='rejected' if rejected else 'unknown' if missing or conflict else 'conditional' if conditional else 'suitable'
    breakdown=[]
    if order.get('duration_hours') is not None:
        rent=order['duration_hours']*machine['rate_per_hour']
        number(rent)
        breakdown=[{'label':'Аренда (учебный тариф)','amount':round(rent,2)}, {'label':'Доставка (учебная)','amount':machine['delivery_cost']}]
        breakdown.extend({'label':'Доплата: '+rule_id,'amount':e['value']} for rule_id,e in effects if e['kind']=='surcharge')
    total=round(sum(x['amount'] for x in breakdown),2) if breakdown else None
    if total is not None: number(total)
    if missing: reasons.append('Недостаточно данных: '+', '.join(missing))
    return dict(equipment_id=machine['id'],name=machine['name'],status=status,total_cost=total,cost_breakdown=breakdown,reasons=reasons,trace=trace,missing=missing)

def recommend(order,equipment,rules):
    """Return applicable equipment, with rejected alternatives sorted last."""
    order=validate_order(order); normalized=[validate_rule(r) for r in rules]
    if len({r['id'] for r in normalized})!=len(normalized): raise ValueError('Идентификаторы правил должны быть уникальными')
    machines=[_equipment(e) for e in equipment]
    matching=[m for m in machines if order.get('work') is None or order['work'] in m['work']]
    if order.get('work')=='lifting' and order.get('lift_purpose') is not None:
        matching=[m for m in matching if m['lift_purpose']==order['lift_purpose']]
    results=[_recommend_one(order,m,normalized) for m in matching]
    groups={'suitable':0,'conditional':0,'unknown':1,'rejected':2}
    return sorted(results,key=lambda r:(groups[r['status']],r['total_cost'] if r['total_cost'] is not None else float('inf'),r['name']))
