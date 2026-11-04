"""Background work snapshots routing and keeps candidates in review."""
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch
from test_ui_support import StreamlitCase


class ProviderRouting(StreamlitCase):
    def test_job_captures_settings_before_controls_change(self):
        settings=SimpleNamespace(provider='openrouter',model='vendor/model',timeout=37,api_key='secret')
        with patch('stroytech.ui_config.read_settings',return_value=settings):
            self.app.selectbox(key='provider').select('openrouter').run()
            thread=Mock()
            with patch('stroytech.ui_extraction_jobs.threading',SimpleNamespace(Thread=thread)):
                self.button('extract_rules').click().run()
                arguments=thread.call_args.kwargs
            self.app.selectbox(key='provider').select('ollama').run()
        self.assertTrue(arguments['daemon'])
        self.assertEqual(arguments['args'][3:7],('vendor/model','filter_first','openrouter',37))
        with patch('stroytech.extraction.extract_rules',return_value=[]) as extract:
            arguments['target'](*arguments['args'])
        extract.assert_called_once_with(arguments['args'][2],model='vendor/model',pipeline='filter_first',provider='openrouter',timeout=37)
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertTrue(any('Сохранено кандидатов: 0' in item.value for item in self.app.success))

    def test_openrouter_routes_to_existing_review_storage(self):
        settings=SimpleNamespace(provider='openrouter',model='vendor/model',timeout=37,api_key='secret')
        candidate={'id':'remote-test','title':'Гидромолот','conditions':[{'field':'soil','op':'eq','value':'rock'}],'effects':[{'kind':'require','value':'Гидромолот'}],'source':'OpenRouter','entities':[],'intent':'requirement','evidence':'скальный','status':'pending'}
        with patch('stroytech.ui_config.read_settings',return_value=settings), patch('stroytech.extraction.extract_rules',return_value=[candidate]) as extract:
            self.app.selectbox(key='provider').select('openrouter').run()
            self.button('extract_rules').click().run()
            time.sleep(.05)
            self.app.run()
        self.assertFalse(self.app.exception)
        self.assertEqual(extract.call_args.kwargs,{'model':'vendor/model','pipeline':'filter_first','provider':'openrouter','timeout':37})
        self.assertEqual(self.repository.list_candidates()[0]['status'],'pending')
        self.assertFalse(any(rule['id']=='remote-test' for rule in self.repository.list_rules()))
