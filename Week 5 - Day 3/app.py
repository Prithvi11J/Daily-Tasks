import asyncio
import json
import os
import re
import hmac
import streamlit as st
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from agents import ROUTES, create_planner
from workflow import create_team
from approval_store import create_request, get_request, list_requests, decide_request
from agent_memory import build_service_memory
from state_store import save_team_state, load_team_state

load_dotenv()

TEAM_LABELS = {
    'strategy_manager': 'Strategy Team (Manager)',
    'iam': 'Identity & Access Management (IAM)',
    'cloud_sec': 'Cloud Security',
    'network_sec': 'Network Security',
    'endpoint_sec': 'Endpoint Security',
    'data_sec': 'Data Security',
    'prod_sec': 'Product Security',
}


def parse_plan(text: str):
    """Read and validate a JSON routing plan; never execute arbitrary output."""
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.IGNORECASE)
    plan = json.loads(cleaned)
    if not isinstance(plan, dict) or not isinstance(plan.get('requests'), list):
        raise ValueError('The Strategy Manager did not return a valid routing plan.')
    items = []
    for item in plan['requests'][:6]:
        if not isinstance(item, dict):
            continue
        request, team = item.get('request'), item.get('team')
        if isinstance(request, str) and request.strip() and team in ROUTES:
            if not any(existing['request'].lower() == request.strip().lower() for existing in items):
                items.append({'request': request.strip(), 'team': team})
    return items


async def route_support_request(question: str, save_snapshots: bool = False):
    """Strategy plans each intent, then a fresh Swarm handles every scoped request."""
    client = OpenAIChatCompletionClient(model='gpt-4o-mini', temperature=0)
    activity = []
    snapshots = []
    try:
        planner = create_planner(client)
        plan_result = await planner.run(task=question)
        plan_text = str(plan_result.messages[-1].content)
        requests = parse_plan(plan_text)
        activity.append(f'Strategy Team identified {len(requests)} service request(s)')
        results = []
        service_memory = await build_service_memory()
        activity.append('AutoGen ListMemory loaded six fictional service catalog entries')
        for item in requests:
            team = create_team(client, service_memory=service_memory)
            scoped_task = (
                f'Employee request: {item["request"]}\n'
                f'Routing hint from Strategy Team: {item["team"]}. '
                'Handle ONLY this request. Give guidance; do not invent incident details.'
            )
            run = await team.run(task=scoped_task)
            if save_snapshots:
                state_path = save_team_state(await team.save_state())
                snapshots.append(state_path)
                activity.append(f'Saved AutoGen Swarm checkpoint for {item["team"]}')
            specialist_messages = [
                m for m in run.messages
                if getattr(m, 'source', '') in ROUTES
                and isinstance(getattr(m, 'content', None), str)
            ]
            for message in run.messages:
                if type(message).__name__ == 'HandoffMessage':
                    target = getattr(message, 'target', 'unknown')
                    activity.append(f'Strategy Team → {TEAM_LABELS.get(target, target)}')
            if specialist_messages:
                reply = specialist_messages[-1]
                routed_to = reply.source
                answer = clean_answer(reply.content)
            else:
                routed_to = item['team']
                answer = ('No specialist answer was returned. Please confirm the correct '
                          'service owner using your approved support directory.')
                activity.append(f'No specialist answer for {TEAM_LABELS[routed_to]}')
            results.append({'request': item['request'], 'team': routed_to, 'answer': answer})
            activity.append(f'{TEAM_LABELS[routed_to]} completed its response')
        return results, activity, snapshots
    finally:
        await client.close()



def clean_answer(text: str) -> str:
    """Remove termination marker and stray standalone punctuation."""
    text = text.replace('ROUTING_COMPLETE', '')
    return "\n".join(line.strip() for line in text.splitlines() if line.strip() and line.strip() != '.').strip()

def split_answer(text: str):
    fields = {'why': '', 'next': '', 'details': []}
    for line in clean_answer(text).splitlines():
        key = line.lower()
        if key.startswith('why this team:'):
            fields['why'] = line.split(':', 1)[1].strip()
        elif key.startswith('next step:'):
            fields['next'] = line.split(':', 1)[1].strip()
        elif not key.startswith('team:'):
            fields['details'].append(line)
    return fields

def reset_request():
    st.session_state['support_question'] = ''
    st.session_state.pop('last_result', None)
    st.session_state.pop('last_snapshots', None)
    st.session_state.pop('routing_message', None)

TEAM_DESCRIPTIONS = {
    'iam': 'Accounts, SSO, MFA, PAM and service access',
    'cloud_sec': 'Cloud security reviews and configurations',
    'network_sec': 'VPN, firewall rules and network connectivity',
    'endpoint_sec': 'Workstations, laptops and endpoint protection',
    'data_sec': 'Data classification, protection and DLP',
    'prod_sec': 'Application and product security assessments',
}

st.set_page_config(page_title='Cybersecurity Support | Service Desk', page_icon='🛡️', layout='wide', initial_sidebar_state='expanded')
st.markdown("""
<style>
.stApp { background: #091321; color: #eaf1f9; }
.block-container { max-width: 1180px; padding-top: 5.5rem; padding-bottom: 3rem; }
/* Keep Streamlit top toolbar from visually obscuring the page heading. */
[data-testid="stHeader"] { background: #091321; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stSidebar"] { background: #0d1a2b; border-right: 1px solid #24384e; }
[data-testid="stMetric"] { background:#111f31; padding: 12px 16px; border-radius: 12px; border: 1px solid #24384e; }
div[data-testid="stVerticalBlockBorderWrapper"] > div { border-color: #2a3c54; border-radius: 16px; }
.stButton > button[kind="primary"] { border-radius: 10px; background: #2060ba; border: 1px solid #327bd4; }
.stButton > button { border-radius: 10px; }
textarea { border-radius: 12px !important; }
.hero-eyebrow { color:#79b8fb; letter-spacing: .12em; font-size:.79rem; font-weight:700; }
.hero-title { font-size:2.25rem; font-weight:760; margin:.25rem 0 .3rem; }
.hero-sub { color:#a9bfd6; margin-bottom:.9rem; }
.section-kicker { color:#91a9c3; font-size:.8rem; letter-spacing:.08em; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# Sidebar: service directory and demo PAM reviewer.
with st.sidebar:
    st.markdown('### 🛡️ Security Service Desk')
    st.caption('AutoGen • Seven-agent service routing')
    st.divider()
    with st.expander('📚 Service directory · 6 teams', expanded=False):
        for team_key, description in TEAM_DESCRIPTIONS.items():
            st.markdown(f'**{TEAM_LABELS[team_key]}**')
            st.caption(description)
    st.divider()
    st.markdown('#### 🔐 PAM reviewer (demo)')
    st.caption('This is a simulation. Never enter real company credentials.')
    passcode = os.getenv('DEMO_REVIEWER_PASSCODE', '')
    if not passcode:
        st.info('Set DEMO_REVIEWER_PASSCODE in .env to enable reviewer mode.')
    elif not st.session_state.get('reviewer_ok', False):
        with st.form('reviewer_login'):
            attempt = st.text_input('Reviewer demo passcode', type='password')
            login = st.form_submit_button('Unlock reviewer')
        if login:
            if hmac.compare_digest(attempt, passcode):
                st.session_state['reviewer_ok'] = True
                st.rerun()
            else:
                st.error('Incorrect passcode')
    else:
        st.success('Reviewer mode unlocked')
        if st.button('Lock reviewer mode'):
            st.session_state['reviewer_ok'] = False
            st.rerun()
        for record in list_requests():
            with st.expander(f"{record['status']} · {record['id'][:8]}"):
                st.write(record['description'])
                st.caption('Created UTC: ' + record['requested_at'])
                if record['status'] == 'PENDING':
                    note = st.text_input('Decision note', key='note_' + record['id'])
                    a, b = st.columns(2)
                    if a.button('Approve', key='approve_' + record['id'], use_container_width=True):
                        decide_request(record['id'], 'APPROVED', note)
                        st.rerun()
                    if b.button('Reject', key='reject_' + record['id'], use_container_width=True):
                        decide_request(record['id'], 'REJECTED', note)
                        st.rerun()
                else:
                    st.write('Decision: ' + record['status'])
                    if record['reviewer_note']:
                        st.caption(record['reviewer_note'])

st.markdown('<div class="hero-eyebrow">CYBERSECURITY / SERVICE ROUTING</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">Security Support Center</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Describe an issue. The Strategy Manager coordinates the right security specialists.</div>', unsafe_allow_html=True)
metric1, metric2, metric3 = st.columns(3)
metric1.metric('Coordination', 'Strategy Manager')
metric2.metric('Specialist coverage', '6 teams')
metric3.metric('Approvals', 'PAM demo only')
st.caption('Prototype with fictional service data. No real tickets, permission changes or approvals are performed.')
st.divider()

st.markdown('### Create a support request')
st.caption('Describe one or more issues in plain language. Avoid credentials, secrets or personal information.')
with st.form('support_form', clear_on_submit=False):
    st.text_area(
        'Describe your cybersecurity issue',
        key='support_question',
        placeholder='For example: My VPN is not connecting and I need a new service account.',
        height=120,
    )
    save_snapshots = st.checkbox('Save AutoGen state checkpoints (fictional data only)', value=False,
                                  help='Checkpoints may contain the query and generated messages.')
    submit = st.form_submit_button('🔎 Find responsible teams', type='primary', use_container_width=True)
reset_col, tip_col = st.columns([1, 4], vertical_alignment='center')
with reset_col:
    st.button('↺ Clear / New request', on_click=reset_request, use_container_width=True)
with tip_col:
    st.caption('Examples: VPN connection • service account • cloud review • device replacement • PAM access')

# Results sit immediately beneath the query, never after a long service-directory section.
if submit:
    question = st.session_state.get('support_question', '').strip()
    if not question:
        st.warning('Enter a support question to continue.')
    elif not os.getenv('OPENAI_API_KEY'):
        st.error('OPENAI_API_KEY is not available in the environment.')
    else:
        with st.status('Strategy Manager is reviewing and routing your request…', expanded=True) as status:
            try:
                st.write('Identifying service requests and contacting specialist agents…')
                results, activity, snapshots = asyncio.run(route_support_request(question, save_snapshots))
                for item in results:
                    is_pam = item['team'] == 'iam' and any(term in item['request'].lower() for term in (
                        'pam', 'privileged', 'administrator access', 'admin access', 'root access',
                        'vault access', 'access secrets', 'production admin', 'elevated access'))
                    if is_pam:
                        item['approval_id'] = create_request(item['request'])
                        activity.append('IAM → PAM request marked PENDING (simulated)')
                st.session_state['last_result'] = (question, results, activity)
                st.session_state['last_snapshots'] = snapshots
                status.update(label=f'Routing completed · {len(results)} request(s) assessed', state='complete', expanded=False)
            except Exception as error:
                status.update(label='Routing failed', state='error', expanded=True)
                st.error(f'{type(error).__name__}: {error}')

if 'last_result' in st.session_state:
    original, results, activity = st.session_state['last_result']
    st.markdown('### ✅ Routing results')
    if not results:
        st.warning('No confident routing match. Please clarify your question or consult the approved support directory.')
    else:
        st.success(f'Analysis complete — {len(results)} service request(s) identified. See the recommended teams below.')
        for index, item in enumerate(results, 1):
            with st.container(border=True):
                st.caption(f'REQUEST {index}')
                st.markdown(f'**{item["request"]}**')
                st.markdown(f'#### {TEAM_LABELS.get(item["team"], item["team"])}')
                sections = split_answer(item['answer'])
                c1, c2 = st.columns(2, gap='large')
                with c1:
                    st.markdown('**Why this team**')
                    st.write(sections['why'] or TEAM_DESCRIPTIONS.get(item['team'], 'Specialist service support'))
                with c2:
                    st.markdown('**Recommended next step**')
                    st.write(sections['next'] or 'Consult the approved support directory for the correct process.')
                if sections['details']:
                    with st.expander('Additional details'):
                        for line in sections['details']:
                            st.write(line)
                if item.get('approval_id'):
                    record = get_request(item['approval_id'])
                    state = record['status'] if record else 'UNKNOWN'
                    st.warning(f'PAM approval: {state} · demonstration only; no access is granted')
                    st.caption('Demo request ID: ' + item['approval_id'])
    with st.expander('🔍 Agent activity · handoffs and responses'):
        for event in activity:
            st.write('• ' + event)
    snapshots = st.session_state.get('last_snapshots', [])
    if snapshots:
        with st.expander('💾 Saved AutoGen state checkpoints'):
            for path in snapshots:
                try:
                    restored = load_team_state(path)
                    st.write('Saved and reloaded: ' + os.path.basename(path))
                    st.caption('Checkpoint keys: ' + ', '.join(restored.keys()))
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    st.warning(f'Could not reload: {exc}')
            st.caption('Checkpoint save/reload does not mean a live conversation automatically resumes.')
else:
    st.info('Your recommended support teams will appear here immediately after you submit the request.')

st.divider()
st.caption('Demo only • AutoGen Swarm + ListMemory • Optional state checkpoints • Local SQLite PAM decisions • Never grant actual access')

# Understand the Important Code
# The service directory is in the sidebar, keeping the result directly under the form.
# st.status() provides immediate execution feedback; st.success() makes completion visible.
# The Clear / New request callback resets the input and last results safely.
# Existing AutoGen multi-intent routing, ListMemory, state checkpoints and PAM demo are preserved.
# Important Notes
# This is a local prototype, not an authenticated production application.
# Use fictional data only; reviewer passcodes are demo-only.
