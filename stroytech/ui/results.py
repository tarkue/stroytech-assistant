"""Recommendation table, explanation and historical inference trace."""
from stroytech.ui.format import display_value, render_rule
from stroytech.ui.labels import LABELS, STATUS
from stroytech.ui.order_data import money

def render_results(results):
    import streamlit as st
    st.divider()
    st.subheader('Результат подбора')
    st.caption('Последний сохранённый расчёт. Изменили условия — выполните подбор ещё раз.')
    rows=[{'Техника':r['name'],'Результат':STATUS[r['status']],'Стоимость':money(r['total_cost'])} for r in results]
    st.dataframe(rows,hide_index=True,width='stretch')
    selected=st.selectbox('Подробности варианта',range(len(results)),format_func=lambda i:results[i]['name'],key='result_choice')
    result=results[selected]
    st.markdown('**'+STATUS[result['status']]+' · '+money(result['total_cost'])+'**')
    for reason in result['reasons']:
        st.write('• '+reason)
    if result['missing']:
        st.write('Уточнить: '+', '.join(LABELS.get(field,field) for field in result['missing']))
    with st.expander('Состав стоимости'):
        st.dataframe([{'Статья':item.get('label',''),'Сумма, ₽':item.get('amount')} for item in result['cost_breakdown']],hide_index=True,width='stretch')
    with st.expander('Трасса вывода и промежуточные факты'):
        if not result['trace']:
            st.write('Правила не сработали.')
        for index,entry in enumerate(result['trace'],1):
            st.markdown(f"**{index}. {entry.get('title',entry.get('rule_id','Правило'))}**")
            if entry.get('conditions') and entry.get('effects'):
                render_rule(entry)
            st.json(entry,expanded=False)
    with st.expander('Факты последнего рассчитанного заказа'):
        order=st.session_state.get('calculated_order',{})
        st.dataframe([{'Параметр':LABELS.get(field,field),'Значение':display_value(field,value)} for field,value in order.items()],hide_index=True,width='stretch')
        st.json(order,expanded=False)
