"""Compare verbose Postman NDJSON request events with the contract subset."""
import json
import sys
from collections import Counter
from pathlib import Path

rows = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
requests = [row for row in rows if row.get('event') == 'request'
            and row.get('method') == 'POST']
assert requests, 'No real client requests reached the simulation'
for row in requests:
    assert row['path'] == '/api/v1/chat/completions'
    assert row['routeKey'] == 'openrouter'
    headers, body = row['requestHeaders'], row['requestBody']
    assert headers['authorization'] == '[REDACTED]'
    assert headers['content-type'] == 'application/json'
    assert body['model'] == 'mock/model' and body['stream'] is False
    assert len(body['messages']) == 1
    assert body['messages'][0]['role'] == 'user'
    assert isinstance(body['messages'][0]['content'], str)
    assert 'При работе на скале требуется гидромолот.' in body['messages'][0]['content']
counts = Counter(row['statusCode'] for row in requests)
assert all(counts[status] for status in (200, 401, 402, 429, 500)), counts
assert any(row.get('duration', 0) >= 1400 for row in requests), 'No delayed timeout response logged'
print(json.dumps({'requests': len(requests), 'status_counts': dict(counts),
                  'contract_subset': 'passed'}, indent=2))
