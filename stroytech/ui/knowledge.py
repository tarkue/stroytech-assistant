"""Approved knowledge and equipment catalogue views."""
from stroytech.ui.format import display_value, render_rule
from stroytech.ui.order_data import money

def render_knowledge(repository):
    import streamlit as st
    rules=repository.list_rules()
    machines=repository.list_equipment()
    st.caption(f'Правила: {len(rules)} · Варианты техники: {len(machines)}')
    st.subheader('Правила')
    query=st.text_input('Поиск по названию или источнику',key='rule_search')
    for rule in rules:
        if query.casefold() not in (rule['title']+' '+rule['source']).casefold():
            continue
        with st.expander(rule['id']+' · '+rule['title']):
            render_rule(rule)
            st.caption('Источник: '+rule['source'])
            with st.expander('Технические данные'):
                st.json(rule)
    st.divider()
    st.subheader('Техника')
    for machine in machines:
        with st.expander(machine['name']):
            st.write('Аренда: '+money(machine['rate_per_hour'])+'/ч · доставка: '+money(machine['delivery_cost']))
            st.write('Работы: '+display_value('work',machine['work']))
            if machine.get('lift_purpose'):
                st.write('Назначение: '+display_value('lift_purpose',machine['lift_purpose']))
            with st.expander('Технические данные'):
                st.json(machine)
