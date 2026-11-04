import json
from pathlib import Path
import unittest
from stroytech.core import recommend
ROOT=Path(__file__).resolve().parents[1]
class CoreTests(unittest.TestCase):
    def setUp(self):
        self.equipment=json.loads((ROOT/'data/equipment.json').read_text()); self.rules=json.loads((ROOT/'data/rules.json').read_text())
        self.order=dict(work='excavation',soil='firm',weather='dry',groundwater=False,near_powerline=False,obstacles=False,narrow_access=False,night=False,lighting=True,duration_hours=4)
    def results(self,**changes):
        if changes.get('work')=='lifting' and 'lift_purpose' not in changes: changes['lift_purpose']='cargo'
        return recommend(self.order|changes,self.equipment,self.rules)
    def test_rock_requires_attachment(self):
        rows=self.results(soil='rock'); self.assertTrue(any(r['status']=='conditional' and r['total_cost']>0 for r in rows)); self.assertTrue(any('гидромолот' in ' '.join(r['reasons']) for r in rows))
    def test_wet_soft_ground_chain(self):
        rows=self.results(work='transport',soil='soft',weather='rain'); self.assertEqual(next(r for r in rows if r['equipment_id']=='truck')['status'],'rejected'); self.assertTrue(any(t.get('rule_id')=='r05' for r in rows for t in r['trace']))
    def test_powerline_overload_and_missing(self):
        rows=self.results(work='lifting',near_powerline=True,load_t=1,radius_m=5,angle_deg=60); self.assertTrue(any(r['status']=='conditional' for r in rows))
        rows=self.results(work='lifting',load_t=100,radius_m=5,angle_deg=60); self.assertTrue(all(r['status']=='rejected' for r in rows))
        rows=self.results(work='lifting'); self.assertTrue(all(r['status']=='unknown' and 'load_t' in r['missing'] for r in rows))
    def test_duration_and_unknown_never_safe(self):
        for value in [0,-1,float('nan'),True]:
            with self.assertRaises(ValueError): self.results(duration_hours=value)
        rows=recommend({'work':'excavation'},self.equipment,self.rules); self.assertTrue(all(r['status']=='unknown' and r['total_cost'] is None for r in rows))
    def test_cost_and_unique_firing(self):
        r=self.results()[0]; self.assertEqual(r['total_cost'],sum(x['amount'] for x in r['cost_breakdown']))
        ids=[t['rule_id'] for t in r['trace'] if 'rule_id' in t]; self.assertEqual(len(ids),len(set(ids)))
    def test_lifting_positive_dimensions_and_numeric_overflow(self):
        for changes in [dict(load_t=0),dict(radius_m=0),dict(duration_hours=1e308)]:
            with self.assertRaises(ValueError): self.results(**(dict(work='lifting',load_t=1,radius_m=5,angle_deg=60)|changes))
    def test_reverse_order_requires_another_pass_and_cycles_terminate(self):
        base=dict(title='t',source='expert')
        rules=[dict(base,id='conclusion',conditions=[dict(field='access_risk',op='eq',value=True)],effects=[dict(kind='require',value='mat')]),dict(base,id='derive',conditions=[dict(field='soil',op='eq',value='firm')],effects=[dict(kind='fact',value=dict(field='access_risk',value=True))])]
        rows=recommend(self.order,self.equipment,rules)
        self.assertEqual([t['rule_id'] for t in rows[0]['trace']],['derive','conclusion'])
    def test_chart_boundary_is_conservative_and_unknown_outside(self):
        rows=self.results(work='lifting',load_t=13,radius_m=5,angle_deg=60)
        self.assertEqual(next(r for r in rows if r['equipment_id']=='crane-25')['status'],'rejected')
        rows=self.results(work='lifting',load_t=1,radius_m=100,angle_deg=60)
        self.assertTrue(all(r['status']=='unknown' and 'capacity_table' in r['missing'] for r in rows))
    def test_inherited_equipment_fact_conflict_is_unknown_and_preserved(self):
        rule=dict(id='conflict',title='contradiction',source='test',conditions=[dict(field='soil',op='eq',value='firm')],effects=[dict(kind='fact',value=dict(field='heavy',value=False))])
        rows=recommend(self.order,self.equipment,[rule])
        heavy=next(r for r in rows if r['equipment_id']=='exc-track')
        self.assertEqual(heavy['status'],'unknown')
        self.assertTrue(heavy['trace'][0]['facts_after']['heavy'])
        self.assertIn('conflict',heavy['trace'][0])
    def test_r05_is_not_a_general_groundwater_or_manipulator_ban(self):
        rows=self.results(work='transport',soil='firm',weather='dry',groundwater=True)
        self.assertTrue(all(r['status']=='conditional' for r in rows))
        rows=self.results(work='transport',soil='soft',weather='rain')
        self.assertEqual(next(r for r in rows if r['equipment_id']=='truck')['status'],'rejected')
        self.assertEqual(next(r for r in rows if r['equipment_id']=='manipulator')['status'],'conditional')
    def test_lift_purpose_is_required_and_platform_not_cargo_crane(self):
        lifting=dict(work='lifting',load_t=0.1,radius_m=5,angle_deg=60)
        cargo=self.results(**lifting,lift_purpose='cargo')
        self.assertEqual({r['equipment_id'] for r in cargo},{'crane-25','crane-50','manipulator'})
        people=self.results(**lifting,lift_purpose='people')
        self.assertEqual([r['equipment_id'] for r in people],['aerial-platform'])
        self.assertEqual(people[0]['status'],'conditional')
        unknown=self.results(**lifting,lift_purpose=None)
        self.assertTrue(all(r['status']=='unknown' and 'lift_purpose' in r['missing'] for r in unknown))
        overload=self.results(**(lifting|dict(load_t=0.3)),lift_purpose='people')
        self.assertEqual(overload[0]['status'],'rejected')
