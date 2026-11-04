import tempfile
import unittest
from pathlib import Path
from stroytech.storage import Repository
from stroytech.core import recommend

def candidate(value=True, title='rule'):
    return dict(id='new-rule',title=title,conditions=[dict(field='soil',op='eq',value='rock')],effects=[dict(kind='fact',value=dict(field='access_risk',value=value))],source='expert',entities=[dict(text='скала',type='soil')],intent='ограничение',evidence='На скале риск подъезда',status='pending')

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=Path(self.tmp.name)/'db.sqlite'; self.repo=Repository(self.path); self.repo.initialize()
    def tearDown(self): self.tmp.cleanup()
    def test_seed_idempotent_and_persistence(self):
        count=len(self.repo.list_rules()); self.repo.initialize(); self.assertEqual(len(self.repo.list_rules()),count)
        self.assertEqual(len(Repository(self.path).list_equipment()),11)
    def test_candidate_confirmation_changes_reloaded_inference(self):
        rule=candidate(); rule['effects']=[dict(kind='reject',value='Учебное экспертное ограничение скалы')]
        ids=self.repo.add_candidates([rule],'На скале нельзя'); self.assertIsInstance(ids[0],int)
        self.assertEqual(self.repo.list_candidates()[0]['status'],'pending'); self.repo.approve_candidate(ids[0])
        other=Repository(self.path); self.assertEqual(other.list_candidates()[0]['status'],'approved')
        order=dict(work='excavation',soil='rock',weather='dry',groundwater=False,near_powerline=False,obstacles=False,narrow_access=False,night=False,duration_hours=4)
        rows=recommend(order,other.list_equipment(),other.list_rules()); self.assertTrue(all(r['status']=='rejected' for r in rows))
        self.assertIsInstance(other.save_order(order,rows),int)
    def test_duplicate_rechecked_on_approval(self):
        a,b=self.repo.add_candidates([candidate(),candidate(title='renamed')],'text'); self.repo.approve_candidate(a)
        with self.assertRaises(ValueError): self.repo.approve_candidate(b)
    def test_conflict_rechecked_on_approval(self):
        a,b=self.repo.add_candidates([candidate(),candidate(False)],'text'); self.repo.approve_candidate(a)
        with self.assertRaises(ValueError): self.repo.approve_candidate(b)
    def test_atomic_batch_invalid_and_reject(self):
        with self.assertRaises(ValueError): self.repo.add_candidates([candidate(),{}],'text')
        self.assertEqual(self.repo.list_candidates(),[])
        cid=self.repo.add_candidates([candidate()],'text')[0]; self.repo.reject_candidate(cid)
        with self.assertRaises(ValueError): self.repo.approve_candidate(cid)
    def test_existing_conflicts_are_staged_and_cannot_be_approved(self):
        cid=self.repo.add_candidates([candidate()],'text')[0]; self.repo.approve_candidate(cid)
        conflicting=self.repo.add_candidates([candidate(False)],'opposite')[0]
        item=next(c for c in self.repo.list_candidates() if c['id']==conflicting)
        self.assertEqual(item['status'],'conflict')
        with self.assertRaises(ValueError): self.repo.approve_candidate(conflicting)
    def test_two_repositories_serialize_duplicate_approvals(self):
        from concurrent.futures import ThreadPoolExecutor
        a,b=self.repo.add_candidates([candidate(),candidate()],'text')
        def approve(cid):
            try: Repository(self.path).approve_candidate(cid); return True
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(approve,[a,b]))
        self.assertEqual(sorted(result),[False,True])
        self.assertEqual(sum(r['id'].startswith('expert-') for r in self.repo.list_rules()),1)
    def test_connection_is_closed_after_success_and_exception(self):
        import sqlite3
        with self.repo._connect() as connection:
            connection.execute('SELECT 1')
        with self.assertRaises(sqlite3.ProgrammingError): connection.execute('SELECT 1')
        with self.assertRaises(RuntimeError):
            with self.repo._connect() as failed:
                raise RuntimeError('rollback and close')
        with self.assertRaises(sqlite3.ProgrammingError): failed.execute('SELECT 1')
    def test_upgrade_keeps_expert_rules_orders_and_candidates(self):
        import json
        rule=candidate(); rule['effects']=[dict(kind='warn',value='Сохранить экспертное правило')]
        cid=self.repo.add_candidates([rule],'expert source')[0]; expert=self.repo.approve_candidate(cid)
        order_id=self.repo.save_order(dict(work='excavation',duration_hours=2),[])
        with self.repo._connect() as connection:
            connection.execute("DELETE FROM metadata WHERE key='seed_version'")
            connection.execute("DELETE FROM equipment WHERE id='aerial-platform'")
            for row in connection.execute('SELECT id,payload FROM equipment').fetchall():
                equipment=json.loads(row['payload']); equipment.pop('lift_purpose',None)
                if equipment['id']=='crane-25': equipment['rate_per_hour']=4321
                connection.execute('UPDATE equipment SET payload=? WHERE id=?',(json.dumps(equipment),row['id']))
        self.repo.initialize(); self.repo.initialize()
        self.assertEqual(len(self.repo.list_equipment()),11)
        crane=next(e for e in self.repo.list_equipment() if e['id']=='crane-25')
        self.assertEqual(crane['lift_purpose'],'cargo'); self.assertEqual(crane['rate_per_hour'],4321)
        self.assertTrue(any(r['id']==expert for r in self.repo.list_rules()))
        self.assertEqual(self.repo.list_candidates()[0]['status'],'approved')
        with self.repo._connect() as connection:
            self.assertIsNotNone(connection.execute('SELECT id FROM orders WHERE id=?',(order_id,)).fetchone())
    def test_legacy_seed_rule_corrections_are_migrated(self):
        import json
        from stroytech.validation import semantic_key
        with self.repo._connect() as connection:
            connection.execute("DELETE FROM metadata WHERE key='seed_version'")
            connection.execute("DELETE FROM rules WHERE id='r23'")
            for row in connection.execute("SELECT id,payload FROM rules WHERE id IN ('r04','r05','r06')").fetchall():
                old=json.loads(row['payload']); old['source']='Учебная БЗ: вариант 2025_Б16, дополнительные условия авторов; требует экспертной проверки.'
                if old['id']=='r05':
                    old['conditions']=[dict(field='access_risk',op='eq',value=True),dict(field='equipment_type',op='in',value=['truck','mixer','manipulator'])]
                connection.execute('UPDATE rules SET payload=?,semantic_key=? WHERE id=?',(json.dumps(old),semantic_key(old),old['id']))
        self.repo.initialize()
        rules={r['id']:r for r in self.repo.list_rules()}
        self.assertIn('r23',rules)
        self.assertIn('Дополнительное консервативное',rules['r04']['source'])
        self.assertIn('Дополнительное консервативное',rules['r06']['source'])
        condition=next(c for c in rules['r05']['conditions'] if c['field']=='equipment_type')
        self.assertNotIn('manipulator',condition['value'])
