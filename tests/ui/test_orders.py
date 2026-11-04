"""Saved recommendations, lift purpose and unknown inputs."""
from tests.ui.support import StreamlitCase
from contextlib import closing

class Orders(StreamlitCase):
    def test_recommendation_saved_and_survives_rerun(self):
        self.button('demo').click().run()
        self.button('submit_order').click().run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.session_state['results'])
        self.assertTrue(self.app.dataframe)
        self.assertIn('сохранен',' '.join(x.value for x in self.app.success))
        results=self.app.session_state['results']
        self.app.selectbox(key='result_choice').select(0).run()
        self.assertEqual(self.app.session_state['results'],results)
        self.assertTrue(any('Трасса' in x.label for x in self.app.expander))
        import sqlite3
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute('SELECT count(*) FROM orders').fetchone()[0],1)

    def test_people_lifting_uses_platform_and_keeps_purpose(self):
        self.button('demo').click().run()
        self.app.selectbox(key='lift_purpose').select('Люди и инструмент')
        self.app.text_input(key='load_t').input('0,2')
        self.button('submit_order').click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state['calculated_order']['lift_purpose'],'people')
        results=self.app.session_state['results']
        self.assertEqual(len(results),1)
        self.assertIn('Автовышка',results[0]['name'])

    def test_unknown_and_invalid_input_are_visible(self):
        self.app.text_input(key='duration_hours').input('0')
        self.button('submit_order').click().run()
        self.assertTrue(self.app.error)
        self.assertFalse(self.app.exception)
        self.app.text_input(key='duration_hours').input('8')
        self.button('submit_order').click().run()
        self.assertTrue(all(row['status']=='unknown' for row in self.app.session_state['results']))
