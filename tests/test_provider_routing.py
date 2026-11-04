"""Both neural stages select one backend and keep legacy positional calls."""
import json
import os
import unittest
from unittest.mock import patch
from stroytech.extraction import extract_rules

class ProviderRoutingTests(unittest.TestCase):
    def test_openrouter_both_orders_do_not_call_ollama(self):
        text = 'При дожде осторожно'
        candidate = dict(id='one', title='Дождь', source='text',
                         conditions=[dict(field='weather', op='eq', value='rain')],
                         effects=[dict(kind='warn', value='Осторожно')], entities=[],
                         intent='restriction', evidence=text, status='pending')
        rules = json.dumps({'rules': [candidate]}, ensure_ascii=False)
        env = dict(OPENROUTER_API_KEY='test-only-key', OPENROUTER_MODEL='vendor/model')
        for pipeline in ('filter_first', 'extract_first'):
            responses = [json.dumps({'text': text}), rules] if pipeline == 'filter_first' else [rules, rules]
            with patch.dict(os.environ, env, clear=True), patch('stroytech.extraction._ensure_installed') as installed:
                with patch('stroytech.extraction._call_openrouter', side_effect=responses) as remote:
                    result = extract_rules(text, pipeline=pipeline, provider='openrouter')
            self.assertEqual(remote.call_count, 2)
            expected = ['filter', 'extract'] if pipeline == 'filter_first' else ['extract', 'filter']
            self.assertEqual([call.args[3] for call in remote.call_args_list], expected)
            self.assertIn('OpenRouter vendor/model', result[0]['source'])
            installed.assert_not_called()

    def test_explicit_local_provider_ignores_remote_environment(self):
        with patch.dict(os.environ, {'STROYTECH_PROVIDER': 'openrouter'}, clear=True):
            with patch('stroytech.extraction._ensure_installed') as installed:
                with patch('stroytech.extraction._call_model', side_effect=['{"text":""}', '{"rules":[]}']):
                    self.assertEqual(extract_rules('нет правил', 'local-model', 'filter_first', provider='ollama'), [])
            installed.assert_called_once_with('local-model')
