import unittest
from stroytech.validation import validate_rule, find_conflicts

def rule(value=True, conditions=None):
    return dict(id='x', title='test', conditions=conditions or [{'field':'load_t','op':'gt','value':2}], effects=[{'kind':'fact','value':{'field':'access_risk','value':value}}], source='expert')

class ValidationTests(unittest.TestCase):
    def test_numeric_overlap_and_disjoint(self):
        self.assertTrue(find_conflicts(rule(), [rule(False,[{'field':'load_t','op':'lt','value':3}])]))
        self.assertFalse(find_conflicts(rule(), [rule(False,[{'field':'load_t','op':'lte','value':2}])]))
    def test_complementary_advice_is_compatible(self):
        a=rule(); b=rule(); a['effects']=[{'kind':'reject','value':'no'}]; b['effects']=[{'kind':'require','value':'mat'}]
        self.assertEqual(find_conflicts(a,[b]),[])
    def test_unsafe_nonfinite_and_unknown_field(self):
        for field,value in [('load_t',float('nan')),('python','x')]:
            r=rule(conditions=[{'field':field,'op':'eq','value':value}])
            with self.assertRaises(ValueError): validate_rule(r)
    def test_malformed_shapes_always_raise_valueerror(self):
        for update in [dict(conditions=[{'field':[],'op':'eq','value':1}]),dict(conditions=[{'field':'load_t','op':[],'value':1}]),dict(effects=[{'kind':[],'value':1}]),dict(effects=[{'kind':'fact','value':{'field':[],'value':True}}])]:
            with self.assertRaises(ValueError): validate_rule(rule()|update)
    def test_semantic_duplicate_ignores_list_order_and_singleton_in(self):
        from stroytech.validation import semantic_key
        a=rule(conditions=[{'field':'soil','op':'in','value':['rock','soft']}])
        b=rule(conditions=[{'field':'soil','op':'in','value':['soft','rock']}])
        self.assertEqual(semantic_key(a),semantic_key(b))
    def test_numeric_domain_angle_not_over_ninety(self):
        with self.assertRaises(ValueError): validate_rule(rule(conditions=[{'field':'angle_deg','op':'gt','value':90}]))
    def test_oversized_number_raises_valueerror(self):
        with self.assertRaises(ValueError): validate_rule(rule(conditions=[{'field':'load_t','op':'eq','value':10**1000}]))
    def test_categorical_disjoint_rules_and_boundary_overlap(self):
        a=rule(conditions=[{'field':'soil','op':'eq','value':'rock'}])
        b=rule(False,[{'field':'soil','op':'eq','value':'soft'}])
        self.assertFalse(find_conflicts(a,[b]))
        a=rule(conditions=[{'field':'load_t','op':'gte','value':2}])
        b=rule(False,[{'field':'load_t','op':'lte','value':2}])
        self.assertTrue(find_conflicts(a,[b]))
    def test_numeric_domain_edges_use_finite_representable_samples(self):
        validate_rule(rule(conditions=[{'field':'angle_deg','op':'gt','value':89.9}]))
        validate_rule(rule(conditions=[{'field':'load_t','op':'gt','value':1e308},{'field':'load_t','op':'lt','value':1.1e308}]))
        for field in ('load_t','radius_m','duration_hours'):
            with self.assertRaises(ValueError): validate_rule(rule(conditions=[{'field':field,'op':'eq','value':0}]))
