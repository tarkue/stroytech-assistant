"""Streamlit entry point and backwards-compatible public UI imports."""
from .ui_labels import BOOL_FIELDS, CHOICES, LABELS, NUM_FIELDS, PURPOSE, STATUS
from .ui_order_data import database_path, money, parse_order
from .ui_order_actions import demo_order, submit_order
from .ui_format import condition_text, display_value, effect_text, render_rule
from .ui_order import render_order
from .ui_results import render_results
from .ui_knowledge import render_knowledge
from .ui_extraction_jobs import extraction_worker, poll_extraction, start_extraction
from .ui_review_actions import review_candidate
from .ui_candidates import render_candidates
from .ui_acquisition import render_acquisition
from .ui_theme import STYLE

def main():
    import streamlit as st
    from .storage import Repository
    st.set_page_config(page_title='Подбор строительной техники',layout='wide',initial_sidebar_state='collapsed')
    st.html(STYLE)
    try:
        repository=Repository(database_path())
        repository.initialize()
    except Exception as exc:
        st.error('Не удалось открыть локальную базу: '+str(exc)+' Проверьте права на каталог data или STROYTECH_DB.')
        return

    st.title('Подбор строительной техники')
    st.caption('Цены и грузовые характеристики — учебные; для реальных работ нужна проверка специалиста.')
    order,knowledge,acquisition=st.tabs(['Подбор техники','База знаний','Правила из текста'])
    with order:
        render_order(repository)
    with knowledge:
        render_knowledge(repository)
    with acquisition:
        st.fragment(run_every=1)(render_acquisition)(repository)
