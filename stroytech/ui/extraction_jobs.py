"""Background extraction work and session event delivery."""
import queue
import threading
from stroytech.ui.config import extraction_settings

def extraction_worker(events,path,source,model,pipeline,provider="ollama",timeout=120):
    """No Streamlit calls here; model output is persisted before completion notice."""
    try:
        from stroytech.extraction import extract_rules
        from stroytech.storage import Repository
        candidates=extract_rules(source,model=model,pipeline=pipeline,provider=provider,timeout=timeout)
        ids=Repository(path).add_candidates(candidates,source)
        events.put(('success',f'Сохранено кандидатов: {len(ids)}. Требуется проверка эксперта.'))
    except Exception as exc:
        hint='Проверьте модель, ключ OPENROUTER_API_KEY и доступ к OpenRouter.' if provider=='openrouter' else 'Проверьте ollama list и имя установленной модели.'
        events.put(('error','Извлечение не завершено: '+str(exc)+' '+hint+' Повторите запрос.'))


def start_extraction(repository):
    import streamlit as st
    source=st.session_state['source_text'].strip()
    model=st.session_state['model'].strip()
    provider=st.session_state.get('provider','ollama')
    try:
        settings=extraction_settings(source,model,provider)
    except ValueError as exc:
        st.session_state['extraction_notice']=('error',str(exc))
        return
    events=queue.Queue()
    st.session_state['extraction_job']=events
    st.session_state.pop('extraction_notice',None)
    threading.Thread(target=extraction_worker,args=(events,repository.path,source,model,st.session_state['pipeline'],provider,settings.timeout),daemon=True).start()


def poll_extraction():
    import streamlit as st
    events=st.session_state.get('extraction_job')
    if events is None:
        return
    try:
        notice=events.get_nowait()
    except queue.Empty:
        return
    st.session_state['extraction_notice']=notice
    st.session_state['extraction_job']=None
