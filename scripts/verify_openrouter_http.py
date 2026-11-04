"""Exercise real urllib transport against an already-running local simulation."""
import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stroytech import openrouter
from stroytech.extraction import extract_rules
from stroytech.extraction_schema import ExtractionError

BASE = 'http://127.0.0.1:43187/openrouter'
TEXT = 'При работе на скале требуется гидромолот.'


def main():
    # Test-process-only endpoint substitution: production host and opener stay intact.
    original = openrouter.ENDPOINT
    openrouter.ENDPOINT = BASE + '/api/v1/chat/completions'
    os.environ['OPENROUTER_API_KEY'] = 'synthetic-local-only'
    results = []
    try:
        for scenario in ('success', 'success-reverse', 'http401', 'http402', 'http429', 'http500',
                         'bad-envelope', 'bad-content', 'empty-content', 'timeout'):
            with urlopen(BASE + '/__control/' + ('success' if scenario == 'success-reverse' else scenario), timeout=2) as response:
                assert response.status == 200
            transcript = []
            try:
                rules = extract_rules(TEXT, provider='openrouter', model='mock/model',
                                      timeout=0.2, transcript=transcript,
                                      pipeline='extract_first' if scenario == 'success-reverse' else 'filter_first')
                assert scenario.startswith('success'), scenario
                assert len(rules) == 1 and rules[0]['status'] == 'pending'
                assert len(transcript) == 2
                outcome = 'one pending rule; two stages'
            except ExtractionError as exc:
                assert not scenario.startswith('success'), str(exc)
                outcome = str(exc)
                if scenario.startswith('http'):
                    assert scenario[4:] in outcome
                if scenario == 'timeout':
                    assert transcript[-1]['error'] == 'network_or_timeout'
            assert 'synthetic-local-only' not in json.dumps(transcript)
            results.append({'scenario': scenario, 'outcome': outcome,
                            'stages': [entry['stage'] for entry in transcript]})
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        openrouter.ENDPOINT = original


if __name__ == '__main__':
    main()
