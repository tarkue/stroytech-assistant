"""Malformed input, model availability and knowledge acquisition integration."""
import json
import subprocess
import unittest
from unittest.mock import patch
from stroytech.extraction import ExtractionError, extract_rules, parse_candidates
from test_extraction import candidate


class OfflineModelTests(unittest.TestCase):
    @patch('stroytech.extraction.subprocess.run')
    def test_missing_model_fails_before_run_no_download(self, run):
        run.return_value=subprocess.CompletedProcess([],1,'','model not found')
        with self.assertRaises(ExtractionError): extract_rules('abc',model='missing')
        self.assertEqual(run.call_count,1)
        self.assertEqual(run.call_args.args[0],['ollama','show','missing'])


class MalformedShapeTests(unittest.TestCase):
    def test_unhashable_fields_and_missing_effect_values_are_domain_errors(self):
        for field in ([], {}, None):
            rule=candidate();rule['conditions'][0]['field']=field
            with self.assertRaises(ExtractionError): parse_candidates(json.dumps({'rules':[rule]}))

    def test_extreme_numeric_value_is_domain_error(self):
        rule=candidate();rule['effects']=[dict(kind='surcharge',value=10**1000)]
        with self.assertRaises(ExtractionError): parse_candidates(json.dumps({'rules':[rule]}))

class LiftPurposeTests(unittest.TestCase):
    def test_people_purpose_uses_shared_schema(self):
        rule=candidate();rule['conditions']=[dict(field='lift_purpose',op='eq',value='people')]
        self.assertEqual(parse_candidates(json.dumps({'rules':[rule]}))[0]['conditions'][0]['value'],'people')
        rule['conditions'][0]['value']='anything'
        with self.assertRaises(ExtractionError):parse_candidates(json.dumps({'rules':[rule]}))

class ConflictAcquisitionTests(unittest.TestCase):
    def test_overlapping_corpus_candidates_require_expert_conflict_review(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from stroytech.storage import Repository
        from stroytech.validation import find_conflicts
        corpus=json.loads((Path(__file__).resolve().parents[1]/'data/extraction_cases.json').read_text())
        overlap=next(case for case in corpus['cases'] if case['id']=='overlap')
        candidates=[dict(candidate(),id='overlap-'+str(i),title='Противоречие '+str(i),conditions=gold['conditions'],effects=gold['effects'],evidence=overlap['text']) for i,gold in enumerate(overlap['gold'])]
        parsed=parse_candidates(json.dumps({'rules':candidates}))
        self.assertEqual(find_conflicts(parsed[1],[parsed[0]]),['overlap-0'])
        with TemporaryDirectory() as folder:
            repo=Repository(Path(folder)/'knowledge.sqlite3');repo.initialize()
            before=len(repo.list_rules())
            ids=repo.add_candidates(parsed,overlap['text'])
            self.assertEqual(len(repo.list_rules()),before)
            repo.approve_candidate(ids[0])
            with self.assertRaisesRegex(ValueError,'Противоречие'):repo.approve_candidate(ids[1])
            self.assertEqual(len(repo.list_rules()),before+1)
            self.assertNotEqual(next(c for c in repo.list_candidates() if c['id']==ids[1])['status'],'approved')
