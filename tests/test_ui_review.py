"""Expert decisions and duplicate feedback."""
from test_ui_support import StreamlitCase


class Review(StreamlitCase):
    def test_candidate_preview_approval_and_rejection(self):
        candidate={'id':'ui-rule','title':'Ночная надбавка','conditions':[{'field':'night','op':'eq','value':True}], 'effects':[{'kind':'surcharge','value':123}], 'source':'UI test','entities':[], 'intent':'pricing','evidence':'Ночью доплата 123 рубля','status':'pending'}
        ids=self.repository.add_candidates([candidate],candidate['evidence'])
        self.app.run()
        self.app.selectbox(key='candidate_choice').select(ids[0]).run()
        self.assertTrue(any('Ночью доплата' in x.value for x in self.app.markdown))
        self.button('approve_candidate').click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.repository.list_candidates()[0]['status'],'approved')
        self.assertTrue(any(r['id']=='expert-'+str(ids[0]) for r in self.repository.list_rules()))
        candidate['id']='second'
        candidate['effects']=[{'kind':'surcharge','value':124}]
        second=self.repository.add_candidates([candidate],candidate['evidence'])[0]
        self.app.run()
        self.app.selectbox(key='candidate_choice').select(second).run()
        self.button('reject_candidate').click().run()
        self.assertEqual(self.repository.list_candidates()[0]['status'],'rejected')

    def test_duplicate_approval_is_visible_and_does_not_change_knowledge(self):
        candidate=dict(self.repository.list_rules()[0],entities=[],intent='test',evidence='Учебный источник',status='pending')
        count=len(self.repository.list_rules())
        identifier=self.repository.add_candidates([candidate],candidate['evidence'])[0]
        self.app.run()
        self.app.selectbox(key='candidate_choice').select(identifier).run()
        self.button('approve_candidate').click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('дубликат' in error.value for error in self.app.error))
        self.assertEqual(len(self.repository.list_rules()),count)
        self.assertEqual(self.repository.list_candidates()[0]['status'],'pending')
