"""Expert approval and rejection callback."""


def review_candidate(repository,candidate_id,approve):
    import streamlit as st
    try:
        method=repository.approve_candidate if approve else repository.reject_candidate
        method(candidate_id)
        st.session_state['refresh_knowledge']=True
        st.session_state['review_notice']=('success','Кандидат подтвержден и включен в БЗ.' if approve else 'Кандидат отклонен.')
    except Exception as exc:
        st.session_state['review_notice']=('error','Не удалось изменить статус: '+str(exc)+' Проверьте дубликаты и конфликты в БЗ.')
