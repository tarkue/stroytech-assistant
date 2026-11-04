"""Provider controls and extraction configuration, without network access."""
from stroytech.config import read_settings


def selected_settings(provider):
    import streamlit as st
    try:
        return read_settings(provider)
    except ValueError as exc:
        st.error(str(exc))
        return None


def render_settings():
    import streamlit as st
    if 'provider' not in st.session_state:
        defaults=selected_settings(None)
        st.session_state['provider']=defaults.provider if defaults else 'ollama'
    provider=st.selectbox('Провайдер',['ollama','openrouter'],format_func=lambda value:{'ollama':'Ollama','openrouter':'OpenRouter'}[value],key='provider')
    settings=selected_settings(provider)
    if st.session_state.get('model_provider') != provider:
        st.session_state['model']=settings.model if settings else ''
        st.session_state['model_provider']=provider
    first,second=st.columns([2,1])
    first.text_input('Модель Ollama' if provider=='ollama' else 'Модель OpenRouter',key='model')
    second.selectbox('Порядок обработки',['filter_first','extract_first'],format_func=lambda value:{'filter_first':'Сначала убрать лишнее','extract_first':'Сначала найти правила'}[value],key='pipeline')
    if provider=='openrouter':
        st.caption('Исходный текст будет отправлен в OpenRouter только после нажатия «Извлечь нейросетью».')
        st.caption('Ключ OpenRouter: '+('настроен' if settings and settings.api_key else 'не настроен; задайте OPENROUTER_API_KEY в окружении.'))


def extraction_settings(source,model,provider):
    settings=read_settings(provider,model=model)
    missing=[]
    if not source:
        missing.append('Введите исходный текст.')
    if not model:
        missing.append('Укажите модель (для OpenRouter задайте OPENROUTER_MODEL).')
    if provider=='openrouter' and not settings.api_key:
        missing.append('Задайте OPENROUTER_API_KEY в окружении.')
    if missing:
        raise ValueError(' '.join(missing))
    return settings
