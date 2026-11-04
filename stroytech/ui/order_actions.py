"""Session callbacks for example orders and saved recommendations."""
from stroytech.ui.labels import BOOL_FIELDS, CHOICES, NUM_FIELDS
from stroytech.ui.order_data import parse_order

def demo_order():
    import streamlit as st
    values={'work':'Подъем','lift_purpose':'Груз','soil':'Мягкий','weather':'Дождь','duration_hours':'8','load_t':'4','radius_m':'6','angle_deg':'45'}
    values.update({field:'Нет' for field in BOOL_FIELDS})
    values['obstacles']='Да'
    for field,value in values.items():
        st.session_state[field]=value


def submit_order(repository):
    import streamlit as st
    from stroytech.core import recommend
    try:
        order=parse_order({field:st.session_state.get(field,'') for field in list(CHOICES)+list(BOOL_FIELDS)+list(NUM_FIELDS)+['lift_purpose']})
        results=recommend(order,repository.list_equipment(),repository.list_rules())
        order_id=repository.save_order(order,results)
        st.session_state['results']=results
        st.session_state['calculated_order']=order
        st.session_state['order_notice']=f'Заказ №{order_id} сохранен. Рассмотрено вариантов: {len(results)}.'
        st.session_state['order_error']=None
        st.session_state['result_choice']=0
    except Exception as exc:
        st.session_state.pop('order_notice',None)
        st.session_state['order_error']='Не удалось выполнить подбор: '+str(exc)+' Исправьте условия и повторите.'
