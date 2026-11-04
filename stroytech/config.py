"""Nonsecret TOML defaults with environment and explicit-call overrides."""
from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import tomllib

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config.toml'

@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    timeout: float
    api_key: str = field(default='', repr=False)


def _defaults():
    if not CONFIG_PATH.exists():
        return {}
    try:
        values = tomllib.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise ValueError('Не удалось прочитать config.toml') from None
    if set(values) - {'provider', 'model', 'timeout'}:
        raise ValueError('config.toml допускает только provider, model, timeout; ключ задаётся через окружение')
    return values


def read_settings(provider=None, *, model=None, timeout=None):
    defaults = _defaults()
    provider = provider if provider is not None else os.environ.get('STROYTECH_PROVIDER', defaults.get('provider', 'ollama'))
    if provider not in ('ollama', 'openrouter'):
        raise ValueError('Провайдер должен быть ollama или openrouter')
    same_provider = defaults.get('provider', 'ollama') == provider
    file_model = defaults.get('model') if same_provider else None
    configured = os.environ.get('OPENROUTER_MODEL', file_model or '') if provider == 'openrouter' else (file_model or 'qwen2.5-coder:7b')
    model = configured if model is None else model
    if not isinstance(model, str) or len(model) > 200 or any(ord(c) < 32 for c in model):
        raise ValueError('Укажите модель в настройках (для OpenRouter — OPENROUTER_MODEL)')
    if provider == 'ollama' and model.startswith('-'):
        raise ValueError('Неверное имя локальной модели')
    raw_timeout = timeout if timeout is not None else os.environ.get('STROYTECH_TIMEOUT', defaults.get('timeout', 120))
    try:
        if isinstance(raw_timeout, bool):
            raise ValueError()
        timeout = float(raw_timeout)
        if not math.isfinite(timeout) or not 0 < timeout <= 600:
            raise ValueError()
    except (ValueError, TypeError, OverflowError):
        raise ValueError('Тайм-аут должен быть числом от 0 (не включая) до 600 секунд') from None
    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip() if provider == 'openrouter' else ''
    if provider == 'openrouter' and (len(api_key) > 4096 or any(ord(c) < 33 or ord(c) > 126 for c in api_key)):
        raise ValueError('Задайте OPENROUTER_API_KEY в окружении')
    if api_key and api_key in model:
        raise ValueError('Имя модели не должно содержать ключ API')
    return Settings(provider, model.strip(), timeout, api_key)


def load_settings(provider=None, *, model=None, timeout=None):
    settings=read_settings(provider,model=model,timeout=timeout)
    if not settings.model:
        raise ValueError('Укажите модель в настройках (для OpenRouter — OPENROUTER_MODEL)')
    if settings.provider=='openrouter' and not settings.api_key:
        raise ValueError('Задайте OPENROUTER_API_KEY в окружении')
    return settings
