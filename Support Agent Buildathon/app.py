"""Single local Streamlit entrypoint. Run: python -m streamlit run app.py"""
import asyncio
import csv
import io
import streamlit as st
import support

st.set_page_config(page_title='Customer Support Agents', page_icon='💬', layout='wide')
st.title('Customer Support Agents')
st.caption('Fictional demo policies · Four actual AutoGen agents · No real store actions')
st.info('Use synthetic complaints only. Submitted text is sent to OpenAI. Escalation flags a local ticket; it does not contact a human automatically.')
for key, default in [('ticket_history', []), ('thread_complaints', []), ('agent_outputs', {}), ('active_ticket', None)]:
    if key not in st.session_state:
        st.session_state[key] = default


def reset_thread():
    st.session_state['thread_complaints'] = []
    st.session_state['active_ticket'] = None
    st.session_state['agent_outputs'] = {}
    st.session_state['submission_mode'] = 'New ticket'
    st.session_state['complaint_input'] = ''


st.button('Start new conversation', key='reset_thread', on_click=reset_thread)
mode = st.radio('Submission type', ['New ticket', 'Follow-up to current ticket'], key='submission_mode', horizontal=True)
if st.session_state.active_ticket:
    st.caption(f'Current ticket: {st.session_state.active_ticket}. A follow-up creates one new linked child ticket/CSV row, never overwrites the parent.')
with st.form('ticket_form'):
    customer_name = st.text_input('Customer name', max_chars=100)
    order_id = st.text_input('Order ID (optional)', max_chars=100)
    complaint = st.text_area('Complaint', max_chars=3000, key='complaint_input')
    submitted = st.form_submit_button('Submit complaint', key='submit')

st.subheader('Live agent outputs')
slots = {}
for phase in ['query', 'knowledge', 'resolution', 'log']:
    with st.expander(phase.title(), expanded=True):
        slots[phase] = st.empty()
        slots[phase].code(st.session_state.agent_outputs.get(phase, 'Waiting'), language=None)

if submitted:
    if not complaint.strip():
        st.error('Please enter a complaint.')
    elif mode == 'Follow-up to current ticket' and not st.session_state.active_ticket:
        st.error('Submit a new ticket before using follow-up.')
    else:
        previous = st.session_state.thread_complaints if mode == 'Follow-up to current ticket' else []
        context = complaint.strip()
        if previous:
            history = '\n'.join(previous)[-1700:]
            context = f'[Follow-up to ticket {st.session_state.active_ticket}]\nPrevious customer context:\n{history}\nCurrent follow-up:\n{context}'
        st.session_state.agent_outputs = {}
        def on_event(phase, text):
            existing = st.session_state.agent_outputs.get(phase, '')
            st.session_state.agent_outputs[phase] = (existing + '\n' + text)[-10000:]
            slots[phase].code(st.session_state.agent_outputs[phase], language=None)
        try:
            with st.spinner('Running Query → Knowledge → Resolution → Log (bounded to 140 seconds)…'):
                row = asyncio.run(support.run_ticket(context, customer_name, order_id, on_event=on_event))
            st.session_state.ticket_history.append(row)
            st.session_state.thread_complaints = (previous + [complaint.strip()])[-4:]
            st.session_state.active_ticket = row['ticket_id']
        except Exception:
            st.error('The ticket could not be completed or saved. Check local configuration, API availability, and writable log permissions. No credentials or raw exception details are shown. Please retry after correcting the issue.')

if st.session_state.active_ticket and st.session_state.ticket_history:
    row = st.session_state.ticket_history[-1]
    st.subheader('Final customer reply')
    if row['status'] == 'Resolved':
        st.success('Resolved')
    else:
        st.warning('Escalated')
    st.write(row['response'])
    st.caption(f"Category: {row['category']} · Urgency: {row['urgency']} · Sentiment: {row['sentiment']}")
    if row['escalation_reason']:
        st.caption(row['escalation_reason'])

st.subheader('Session ticket history / CSV log')
st.caption('Only this browser session’s submissions are displayed/downloaded. The local CSV retains all saved tickets. New conversation clears active context, not history.')
if st.session_state.ticket_history:
    st.dataframe(st.session_state.ticket_history, hide_index=True, width='stretch')
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=support.LOG_COLUMNS)
    writer.writeheader()
    for row in st.session_state.ticket_history:
        safe = {key: "'" + str(row[key]) if str(row[key]).lstrip().startswith(('=', '+', '-', '@')) else row[key] for key in support.LOG_COLUMNS}
        writer.writerow(safe)
    st.download_button('Download session CSV', buffer.getvalue().encode('utf-8'), 'support_tickets.csv', 'text/csv')
else:
    st.caption('No tickets submitted in this session yet. No prebuilt index or log file is required.')
