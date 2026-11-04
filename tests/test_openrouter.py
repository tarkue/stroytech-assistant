"""HTTP transport contract, bounded responses and sanitized failure handling."""
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from stroytech.config import Settings
from stroytech.extraction import ExtractionError
from stroytech.openrouter import call_model, MAX_HTTP_RESPONSE

class OpenRouterTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings('openrouter', 'vendor/model', 12, 'private-test-key')

    def test_request_and_response_redact_echoed_secret(self):
        response = BytesIO(json.dumps({'choices': [{'message': {'content': 'answer private-test-key'}}]}).encode())
        trace = []
        with patch('stroytech.openrouter.urlopen', return_value=response) as opening:
            result = call_model('prompt', self.settings, trace, 'extract')
        request = opening.call_args.args[0]
        self.assertEqual(request.full_url, 'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(request.get_header('Authorization'), 'Bearer private-test-key')
        self.assertEqual(json.loads(request.data), {'model': 'vendor/model', 'messages': [{'role': 'user', 'content': 'prompt'}], 'stream': False})
        self.assertEqual(opening.call_args.kwargs['timeout'], 12)
        self.assertEqual(result, 'answer [REDACTED]')
        self.assertNotIn('private-test-key', str(trace))

    def test_http_and_network_errors_never_echo_http_bodies(self):
        for code in (401, 402, 429, 500, 503, 400, 302):
            error = HTTPError('https://openrouter.ai', code, 'private-test-key', {}, BytesIO(b'private-test-key'))
            trace = []
            with patch('stroytech.openrouter.urlopen', side_effect=error):
                with self.assertRaises(ExtractionError) as caught:
                    call_model('prompt', self.settings, trace, 'extract')
            self.assertIn(str(code), str(caught.exception))
            self.assertNotIn('private-test-key', str(caught.exception) + str(trace))
        for error in (TimeoutError('private-test-key'), URLError('private-test-key')):
            with patch('stroytech.openrouter.urlopen', side_effect=error):
                with self.assertRaises(ExtractionError) as caught:
                    call_model('prompt', self.settings, [], 'extract')
            self.assertNotIn('private-test-key', str(caught.exception))

    def test_empty_malformed_and_large_responses(self):
        for raw in (b'not json', b'{}', b'{"choices":null}', b'{"choices":[]}',
                    b'{"choices":[{"message":{"content":""}}]}', b'x' * (MAX_HTTP_RESPONSE + 1)):
            with self.subTest(size=len(raw)), patch('stroytech.openrouter.urlopen', return_value=BytesIO(raw)):
                with self.assertRaises(ExtractionError):
                    call_model('prompt', self.settings, [], 'filter')
