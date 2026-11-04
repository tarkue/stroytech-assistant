import json
import subprocess
import unittest
from unittest.mock import patch
from stroytech.extraction import ExtractionError, extract_rules, parse_candidates


def candidate():
    return dict(id='r1', title='Rain', conditions=[dict(field='weather',op='eq',value='rain')], effects=[dict(kind='warn',value='Осторожно')],source='text',entities=[dict(text='дождь',type='weather')],intent='restriction',evidence='При дожде осторожно',status='pending')


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        installed=patch("stroytech.extraction._ensure_installed")
        installed.start()
        self.addCleanup(installed.stop)

    def test_valid_candidate(self):
        self.assertEqual(parse_candidates(json.dumps({'rules':[candidate()]}))[0]['status'],'pending')

    def test_rejects_invalid_and_executable_content(self):
        for raw in ['not json', '{"rules":{}}', '{"rules":[{"conditions":[]}]}']:
            with self.assertRaises(ExtractionError): parse_candidates(raw)
        rule=candidate(); rule['conditions'][0]['field']='__import__'
        with self.assertRaises(ExtractionError): parse_candidates(json.dumps({'rules':[rule]}))

    def test_rejects_invalid_enum_and_negative_surcharge(self):
        rule=candidate(); rule['conditions'][0]['value']='sunny'
        with self.assertRaises(ExtractionError): parse_candidates(json.dumps({'rules':[rule]}))
        rule=candidate(); rule['effects']=[dict(kind='surcharge',value=-1)]
        with self.assertRaises(ExtractionError): parse_candidates(json.dumps({'rules':[rule]}))

    @patch('stroytech.extraction.subprocess.run')
    def test_two_orders_and_stdin(self, run):
        run.side_effect=[subprocess.CompletedProcess([],0,'{"text":"При дожде осторожно"}',''),subprocess.CompletedProcess([],0,json.dumps({'rules':[candidate()]}),'')]
        self.assertEqual(len(extract_rules('При дожде осторожно')),1)
        self.assertEqual(run.call_args.args[0][:2],['ollama','run'])
        self.assertIn('input',run.call_args.kwargs)
        self.assertIn('--nowordwrap',run.call_args.args[0])
        run.reset_mock(); run.side_effect=[subprocess.CompletedProcess([],0,json.dumps({'rules':[candidate()]}),''),subprocess.CompletedProcess([],0,json.dumps({'rules':[candidate()]}),'')]
        self.assertEqual(len(extract_rules('При дожде осторожно',pipeline='extract_first')),1)
        self.assertIn('AUDIT',run.call_args.kwargs['input'])

    @patch('stroytech.extraction.subprocess.run')
    def test_process_errors_never_become_empty_success(self, run):
        for error in [FileNotFoundError(), subprocess.TimeoutExpired('ollama',1)]:
            run.side_effect=error
            with self.assertRaises(ExtractionError): extract_rules('дождь')
        run.side_effect=None;run.return_value=subprocess.CompletedProcess([],1,'','server unavailable')
        with self.assertRaisesRegex(ExtractionError,'server unavailable'): extract_rules('дождь')

    def test_empty_input_and_bad_pipeline(self):
        for kwargs in [dict(text=''),dict(text='abc',pipeline='wrong')]:
            with self.assertRaises(ExtractionError): extract_rules(**kwargs)

    @patch('stroytech.extraction.subprocess.run')
    def test_fabricated_filter_or_evidence_rejected(self, run):
        run.return_value=subprocess.CompletedProcess([],0,'{"text":"Придуманный текст"}','')
        with self.assertRaisesRegex(ExtractionError,'изменил'): extract_rules('Оригинал')
        rule=candidate(); rule['evidence']='Отсутствующая цитата'
        run.side_effect=[subprocess.CompletedProcess([],0,'{"text":"Оригинал"}',''),subprocess.CompletedProcess([],0,json.dumps({'rules':[rule]}),'')]
        with self.assertRaisesRegex(ExtractionError,'Цитата'): extract_rules('Оригинал')

    def test_shared_validator_rejects_contradictory_conditions(self):
        rule=candidate();rule['conditions'].append(dict(field='weather',op='eq',value='dry'))
        with self.assertRaises(ExtractionError):parse_candidates(json.dumps({'rules':[rule]}))

    @patch('stroytech.extraction.subprocess.run')
    def test_transcript_preserves_failed_process(self, run):
        run.return_value=subprocess.CompletedProcess([],1,'partial','server refused')
        transcript=[]
        with self.assertRaises(ExtractionError): extract_rules('abc',transcript=transcript)
        self.assertEqual(transcript[0]['raw_response'],'partial')
        self.assertEqual(transcript[0]['stderr'],'server refused')
