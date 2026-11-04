"""Asynchronous extraction error and staging behavior."""
from test_ui_support import StreamlitCase
import time
from unittest.mock import patch

class Acquisition(StreamlitCase):
    def test_background_extraction_error_and_candidate_staging(self):
        from stroytech.extraction import ExtractionError
        with patch('stroytech.extraction.extract_rules',side_effect=ExtractionError('Модель недоступна')):
            self.button('extract_rules').click().run()
            time.sleep(.05)
            self.app.run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('Модель недоступна' in item.value for item in self.app.error))
        candidate={'id':'neural-test','title':'Добавить гидромолот','conditions':[{'field':'soil','op':'eq','value':'rock'}], 'effects':[{'kind':'require','value':'Гидромолот'}], 'source':'test model','entities':[{'text':'скала','type':'soil'}], 'intent':'requirement','evidence':'скала','status':'pending'}
        with patch('stroytech.extraction.extract_rules',return_value=[candidate]):
            self.button('extract_rules').click().run()
            time.sleep(.05)
            self.app.run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.repository.list_candidates()[0]['status'],'pending')
        self.assertFalse(any(rule['id']=='neural-test' for rule in self.repository.list_rules()))
