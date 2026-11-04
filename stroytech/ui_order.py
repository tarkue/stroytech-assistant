"""Order form and its current result."""
from .ui_labels import CHOICES, LABELS, PURPOSE
from .ui_order_actions import demo_order, submit_order
from .ui_results import render_results

def render_order(repository):
    import streamlit as st
    left,right=st.columns([3,1],vertical_alignment='bottom')
    left.selectbox(LABELS['work'],['Неизвестно']+list(CHOICES['work']),key='work')
    right.button('Заполнить пример',key='demo',on_click=demo_order,help='Кран на мягком грунте после дождя')
    lifting=st.session_state['work']=='Подъем'
    if lifting:
        st.selectbox('Что поднимаем?',['Неизвестно']+list(PURPOSE),key='lift_purpose')
    with st.form('order_form',border=False):
        st.markdown('**Площадка**')
        columns=st.columns(2)
        for column,field in zip(columns,('soil','weather')):
            column.selectbox(LABELS[field],['Неизвестно']+list(CHOICES[field]),key=field)
        for fields in (('groundwater','near_powerline'),('obstacles','narrow_access')):
            for column,field in zip(st.columns(2),fields):
                column.selectbox(LABELS[field],['Неизвестно','Да','Нет'],key=field)
        st.markdown('**Режим работы**')
        duration,night,lighting=st.columns(3)
        st.session_state.setdefault('duration_hours','8')
        duration.text_input(LABELS['duration_hours'],key='duration_hours')
        for column,field in ((night,'night'),(lighting,'lighting')):
            column.selectbox(LABELS[field],['Неизвестно','Да','Нет'],key=field)
        if lifting:
            st.markdown('**Параметры подъёма**')
            for column,field in zip(st.columns(3),('load_t','radius_m','angle_deg')):
                st.session_state.setdefault(field,'')
                label='Люди и инструмент, т' if field=='load_t' and st.session_state.get('lift_purpose')=='Люди и инструмент' else LABELS[field]
                column.text_input(label,key=field,placeholder='Неизвестно')
            st.caption('Масса и вылет — больше нуля, угол — от 0 до 90°. Пустое поле означает, что данных пока нет.')
        submitted=st.form_submit_button('Подобрать технику',key='submit_order',type='primary')
    if submitted:
        submit_order(repository)
    if st.session_state.get('order_error'):
        st.error(st.session_state['order_error'])
    if st.session_state.get('order_notice'):
        st.success(st.session_state['order_notice'])
    results=st.session_state.get('results')
    if results is None:
        st.caption('Варианты и стоимость появятся после подбора. Неизвестные условия можно уточнить позже.')
        return
    if not results:
        st.warning('В парке нет техники для выбранных работ.')
        return
    if st.session_state.get('order_error'):
        st.warning('Ниже — предыдущий расчёт. Новые условия ещё не рассчитаны.')
    render_results(results)
