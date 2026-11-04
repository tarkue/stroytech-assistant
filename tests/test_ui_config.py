"""Provider selection never sends source text before explicit extraction."""
from types import SimpleNamespace
from unittest.mock import patch
from test_ui_support import StreamlitCase


class ProviderSettings(StreamlitCase):
    def settings(self, provider=None, **overrides):
        provider=provider or 'ollama'
        return SimpleNamespace(provider=provider, model={'ollama':'local-model', 'openrouter':'vendor/model'}[provider], timeout=37, api_key='private-test-key')

    def test_provider_defaults_key_privacy_and_no_automatic_requests(self):
        with patch('stroytech.ui_config.read_settings',side_effect=self.settings), patch('stroytech.extraction.extract_rules') as extract:
            self.app.selectbox(key='provider').select('openrouter').run()
            self.app.selectbox(key='provider').select('ollama').run()
            self.assertEqual(self.app.text_input(key='model').value,'local-model')
            self.app.selectbox(key='provider').select('openrouter').run()
            self.assertFalse(self.app.exception)
            self.assertEqual(self.app.text_input(key='model').value,'vendor/model')
            captions=' '.join(item.value for item in self.app.caption)
            self.assertIn('Исходный текст будет отправлен в OpenRouter',captions)
            self.assertIn('Ключ OpenRouter: настроен',captions)
            self.assertNotIn('private-test-key',str(self.app))
            extract.assert_not_called()

    def test_missing_key_and_model_give_actionable_notice(self):
        missing=SimpleNamespace(provider='openrouter',model='',timeout=37,api_key=None)
        with patch('stroytech.ui_config.read_settings',return_value=missing), patch('stroytech.extraction.extract_rules') as extract:
            self.app.selectbox(key='provider').select('openrouter').run()
            self.button('extract_rules').click().run()
            self.assertFalse(self.app.exception)
            errors=' '.join(item.value for item in self.app.error)
            self.assertIn('OPENROUTER_API_KEY',errors)
            self.assertIn('модел',errors)
            extract.assert_not_called()

    def test_openrouter_without_configuration_shows_setup_instead_of_crashing(self):
        with patch.dict('os.environ',{'OPENROUTER_MODEL':'','OPENROUTER_API_KEY':''}):
            self.app.selectbox(key='provider').select('openrouter').run()
            self.assertFalse(self.app.exception)
            self.button('extract_rules').click().run()
        self.assertFalse(self.app.exception)
        notices=' '.join(item.value for item in self.app.error)+ ' '.join(item.value for item in self.app.caption)
        self.assertIn('OPENROUTER_MODEL',notices)
        self.assertIn('OPENROUTER_API_KEY',notices)

    def test_entered_model_can_override_missing_environment_default(self):
        with patch.dict('os.environ',{'OPENROUTER_MODEL':'','OPENROUTER_API_KEY':'test-key'}), patch('stroytech.extraction.extract_rules',return_value=[]) as extract:
            self.app.selectbox(key='provider').select('openrouter').run()
            self.app.text_input(key='model').input('vendor/typed-model').run()
            self.button('extract_rules').click().run()
        self.assertTrue(extract.called)

    def test_model_default_visible_without_key_and_key_presence_without_model(self):
        with patch.dict('os.environ',{'OPENROUTER_MODEL':'vendor/configured','OPENROUTER_API_KEY':''}):
            self.app.selectbox(key='provider').select('openrouter').run()
            self.assertEqual(self.app.text_input(key='model').value,'vendor/configured')
            self.assertTrue(any('Ключ OpenRouter: не настроен' in item.value for item in self.app.caption))
        self.app.selectbox(key='provider').select('ollama').run()
        with patch.dict('os.environ',{'OPENROUTER_MODEL':'','OPENROUTER_API_KEY':'private-test-key'}):
            self.app.selectbox(key='provider').select('openrouter').run()
            self.assertTrue(any(item.value=='Ключ OpenRouter: настроен' for item in self.app.caption))
            self.assertNotIn('private-test-key',str(self.app))

    def test_configured_provider_initializes_once_and_user_choice_survives_rerun(self):
        from test_ui_support import ROOT
        with patch.dict('os.environ',{'STROYTECH_PROVIDER':'openrouter','OPENROUTER_MODEL':'','OPENROUTER_API_KEY':''}):
            app=type(self.app).from_file(str(ROOT/'app.py'),default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key='provider').value,'openrouter')
            app.selectbox(key='provider').select('ollama').run()
            app.run()
            self.assertEqual(app.selectbox(key='provider').value,'ollama')
