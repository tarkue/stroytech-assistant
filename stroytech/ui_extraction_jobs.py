"""Background extraction work and session event delivery."""
import queue
import threading

def extraction_worker(events,path,source,model,pipeline):
    """No Streamlit calls here; model output is persisted before completion notice."""
    try:
        from .extraction import extract_rules
        from .storage import Repository
        candidates=extract_rules(source,model=model,pipeline=pipeline)
        ids=Repository(path).add_candidates(candidates,source)
        events.put(('success',f'Сохранено кандидатов: {len(ids)}. Требуется проверка эксперта.'))
    except Exception as exc:
        events.put(('error','Извлечение не завершено: '+str(exc)+' Проверьте ollama list, имя установленной модели и исходный текст; повторите запрос.'))


def start_extraction(repository):
    import streamlit as st
    source=st.session_state['source_text'].strip()
    model=st.session_state['model'].strip()
    if not source or not model:
        st.session_state['extraction_notice']=('error','Введите исходный текст и имя установленной модели Ollama.')
        return
    events=queue.Queue()
    st.session_state['extraction_job']=events
    st.session_state.pop('extraction_notice',None)
    threading.Thread(target=extraction_worker,args=(events,repository.path,source,model,st.session_state['pipeline']),daemon=True).start()


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
