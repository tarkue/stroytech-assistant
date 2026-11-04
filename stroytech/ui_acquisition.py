"""Expert text input and asynchronous acquisition view."""
from .ui_candidates import render_candidates
from .ui_extraction_jobs import poll_extraction, start_extraction

def render_acquisition(repository):
    import streamlit as st
    if st.session_state.pop('refresh_knowledge',False):
        st.rerun()
    poll_extraction()
    st.subheader('Добавить правила')
    st.caption('Опишите условия и ограничения. Извлечённые правила сначала поступят на проверку.')
    st.text_area('Исходный текст',value='Если грунт скальный и выполняются земляные работы, требуется гидромолот.',height=130,key='source_text')
    first,second=st.columns([2,1])
    first.text_input('Локальная модель Ollama',value='qwen2.5-coder:7b',key='model')
    second.selectbox('Порядок обработки',['filter_first','extract_first'],format_func=lambda value:{'filter_first':'Сначала убрать лишнее','extract_first':'Сначала найти правила'}[value],key='pipeline')
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
