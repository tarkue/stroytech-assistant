"""Bounded non-streaming OpenRouter transport; no error bodies are exposed."""
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, build_opener
from stroytech.extraction.schema import ExtractionError, MAX_RESPONSE, PROMPT_VERSION

ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
MAX_HTTP_RESPONSE = 256000

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

urlopen = build_opener(_NoRedirect()).open


def call_model(prompt, settings, transcript, stage):
    key = settings.api_key
    clean = lambda text: text.replace(key, '[REDACTED]') if key else text
    record = dict(stage=stage, provider='openrouter', model=settings.model,
                  prompt=clean(prompt), prompt_version=PROMPT_VERSION)
    transcript.append(record)
    body = dict(model=settings.model, messages=[dict(role='user', content=prompt)], stream=False)
    request = Request(ENDPOINT, data=json.dumps(body).encode('utf-8'), method='POST',
                      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=settings.timeout) as response:
            raw = response.read(MAX_HTTP_RESPONSE + 1)
        if len(raw) > MAX_HTTP_RESPONSE:
            raise ExtractionError('OpenRouter: ответ превышает допустимый размер')
        data = json.loads(raw)
        content = data['choices'][0]['message']['content']
        if not isinstance(content, str) or not content.strip() or len(content) > MAX_RESPONSE:
            raise ExtractionError('OpenRouter: отсутствует допустимый текст ответа')
    except HTTPError as exc:
        status = exc.code
        exc.close()
        message = {401: 'проверьте ключ API', 402: 'недостаточно средств',
                   429: 'превышен лимит запросов'}.get(status, 'ошибка сервиса' if status >= 500 else 'запрос отклонён')
        record['error'] = f'HTTP {status}'
        raise ExtractionError(f'OpenRouter HTTP {status}: {message}') from None
    except (TimeoutError, URLError, OSError):
        record['error'] = 'network_or_timeout'
        raise ExtractionError('OpenRouter: сеть недоступна или истёк тайм-аут') from None
    except (ValueError, KeyError, IndexError, TypeError):
        record['error'] = 'malformed_response'
        raise ExtractionError('OpenRouter: некорректный JSON ответа') from None
    except ExtractionError:
        record['error'] = 'invalid_response'
        raise
    content = clean(content)
    record['raw_response'] = content
    return content
