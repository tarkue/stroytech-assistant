"""Expert text input and asynchronous acquisition view."""
from stroytech.ui.candidates import render_candidates
from stroytech.ui.config import render_settings
from stroytech.ui.extraction_jobs import poll_extraction, start_extraction

def render_acquisition(repository):
    import streamlit as st
    if st.session_state.pop('refresh_knowledge',False):
        st.rerun()
    poll_extraction()
    st.subheader('Добавить правила')
    st.caption('Опишите условия и ограничения. Извлечённые правила сначала поступят на проверку.')
    st.text_area('Исходный текст',value='Если грунт скальный и выполняются земляные работы, требуется гидромолот.',height=130,key='source_text')
    render_settings()
    running=st.session_state.get('extraction_job') is not None
    if st.button('Извлечь нейросетью',key='extract_rules',disabled=running,type='primary'):
        start_extraction(repository)
        running=st.session_state.get('extraction_job') is not None
    if running:
        st.caption('Обработка текста… Можно перейти на другую вкладку; результат сохранится автоматически.')
    if st.session_state.get('extraction_notice'):
        kind,message=st.session_state['extraction_notice']
        getattr(st,kind)(message)
    st.divider()
    render_candidates(repository)
