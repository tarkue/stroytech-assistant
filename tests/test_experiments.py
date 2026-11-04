import unittest
from stroytech.experiments import score_rules

class ExperimentTests(unittest.TestCase):
    def test_order_independent_exact_semantics(self):
        a={'conditions':[{'field':'soil','op':'eq','value':'rock'}], 'effects':[{'kind':'require','value':'Гидромолот'}]}
        b=dict(a,title='different')
        self.assertEqual(score_rules([a,b],[a])['f1'],1)
    def test_missed_and_false_rules(self):
        a={'conditions':[], 'effects':[{'kind':'warn','value':'a'}]}
        b={'conditions':[], 'effects':[{'kind':'warn','value':'b'}]}
        metrics=score_rules([a,b],[a])
        self.assertEqual(metrics['precision'],.5)
        self.assertEqual(metrics['recall'],1)
    def test_negative_case(self):
        self.assertEqual(score_rules([],[])['f1'],1)

    def test_errors_count_as_missed_rules_and_saved_artifacts(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from stroytech.extraction import ExtractionError
        from stroytech.experiments import run_experiment
        gold={'conditions':[{'field':'soil','op':'eq','value':'rock'}],'effects':[{'kind':'require','value':'Гидромолот'}]}
        with TemporaryDirectory() as folder:
            root=Path(folder); (root/'cases.json').write_text(json.dumps({'cases':[{'id':'one','text':'text','gold':[gold]}]}))
            with patch('stroytech.experiments.extract_rules',side_effect=ExtractionError('offline')), patch('stroytech.experiments.subprocess.run',side_effect=OSError()):
                result=run_experiment(root/'cases.json',root/'results')
            for pipeline in ('filter_first','extract_first'):
                self.assertEqual(result['summaries'][pipeline]['errors'],1)
                self.assertEqual(result['summaries'][pipeline]['fn'],1)
                self.assertEqual(result['summaries'][pipeline]['f1'],0)
                self.assertTrue((root/'results'/(pipeline+'-one.json')).exists())

    def test_negative_error_is_not_correct_inference(self):
        import json
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from stroytech.extraction import ExtractionError
        from stroytech.experiments import run_experiment
        with TemporaryDirectory() as folder:
            root=Path(folder); (root/'cases.json').write_text(json.dumps({'cases':[{'id':'negative','text':'narrative','gold':[]}]}))
            with patch('stroytech.experiments.extract_rules',side_effect=ExtractionError('bad JSON')), patch('stroytech.experiments.subprocess.run',side_effect=OSError()):
                summary=run_experiment(root/'cases.json',root/'results')['summaries']['filter_first']
            self.assertEqual(summary['usable_outputs'],0)
            self.assertEqual(summary['negative_cases'],1)
            self.assertEqual(summary['negative_correct'],0)
            self.assertEqual(summary['negative_errors'],1)
            self.assertEqual(summary['exact_cases'],0)
