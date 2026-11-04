"""Candidate review form and human rule preview."""
from .ui_format import render_rule
from .ui_labels import STATUS
from .ui_review_actions import review_candidate

def render_candidates(repository):
    import streamlit as st
    candidates=repository.list_candidates()
    st.subheader('Экспертная проверка')
    if not candidates:
        st.caption('Правил на проверке пока нет.')
        return
    by_id={row['id']:row for row in candidates}
    st.dataframe([{'ID':r['id'],'Правило':r['title'],'Статус':STATUS[r['status']]} for r in candidates],hide_index=True,width='stretch')
    if st.session_state.get('candidate_choice') not in by_id:
        st.session_state['candidate_choice']=candidates[0]['id']
    candidate_id=st.selectbox('Кандидат',list(by_id),format_func=lambda i:f"#{i} · {by_id[i]['title']}",key='candidate_choice')
    candidate=by_id[candidate_id]
    st.caption('Статус: '+STATUS[candidate['status']])
    render_rule(candidate)
    with st.expander('Источник и разбор текста'):
        st.markdown('**Исходный текст:** '+candidate['source_text'])
        if candidate.get('evidence') and candidate['evidence']!=candidate['source_text']:
            st.markdown('**Подтверждающий фрагмент:** '+candidate['evidence'])
        intent=candidate.get('intent','')
        st.write('Намерение: '+{'requirement':'Условие выполнения работ','restriction':'Ограничение','pricing':'Стоимость','recommendation':'Рекомендация','safety':'Безопасность'}.get(intent,intent))
    with st.expander('Технические данные'):
        st.json(candidate)
    can_review=candidate['status'] in ('pending','conflict')
    first,second=st.columns(2)
    first.button('Подтвердить выбранное правило',key='approve_candidate',type='primary',disabled=not can_review,on_click=review_candidate,args=(repository,candidate_id,True),width='stretch')
    second.button('Отклонить выбранное правило',key='reject_candidate',disabled=not can_review,on_click=review_candidate,args=(repository,candidate_id,False),width='stretch')
    if st.session_state.get('review_notice'):
        kind,message=st.session_state['review_notice']
        getattr(st,kind)(message)
