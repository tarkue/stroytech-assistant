"""Local Ollama subprocess transport with explicit failures."""
import subprocess
from stroytech.extraction.schema import ExtractionError, PROMPT_VERSION

def _call_model(prompt, model, timeout, transcript, stage):
    record={'stage':stage,'prompt':prompt,'model':model,'prompt_version':PROMPT_VERSION}
    transcript.append(record)
    try:
        process=subprocess.run(['ollama','run',model,'--format','json','--nowordwrap'],input=prompt,text=True,capture_output=True,timeout=timeout,check=False)
    except FileNotFoundError as exc:
        record['error']='ollama executable unavailable'
        raise ExtractionError('Ollama CLI не найден') from exc
    except subprocess.TimeoutExpired as exc:
        record.update(error='timeout',raw_response=_decode(exc.stdout),stderr=_decode(exc.stderr))
        raise ExtractionError(f'Тайм-аут Ollama ({timeout} с)') from exc
    except OSError as exc:
        record['error']=str(exc)
        raise ExtractionError('Не удалось запустить Ollama: '+str(exc)) from exc
    record.update(raw_response=process.stdout,stderr=process.stderr,returncode=process.returncode)
    if process.returncode:
        raise ExtractionError('Ollama: '+process.stderr.strip()[:1000])
    return process.stdout


def _decode(value):
    return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else (value or '')


def _ensure_installed(model):
    """show never pulls; reject an absent model before ollama run can download it."""
    try:
        result=subprocess.run(['ollama','show',model],capture_output=True,text=True,timeout=10,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ExtractionError('Ollama недоступна: '+str(exc)) from exc
    if result.returncode:
        raise ExtractionError('Локальная модель недоступна (загрузка отключена): '+result.stderr.strip()[:1000])
