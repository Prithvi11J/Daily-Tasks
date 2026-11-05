"""Real API through Streamlit's AppTest; no fake UI backend in this test."""
import json
import os
import pytest
from streamlit.testing.v1 import AppTest
from support import ROOT

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.getenv('RUN_LIVE_TESTS') != '1', reason='Opt-in paid real API UI test')]


def test_live_ui_followup_reset_and_escalation(monkeypatch):
    path = ROOT / 'evidence' / 'synthetic_ui_tickets.csv'
    path.parent.mkdir(exist_ok=True)
    path.unlink(missing_ok=True)
    monkeypatch.setenv('TICKET_LOG_PATH', str(path))
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=160).run()
    app.text_input[0].input('SYNTHETIC APPTEST CUSTOMER')
    app.text_input[1].input('DEMO-UI')
    app.text_area[0].input('The blender I received is broken. Can I get a replacement?')
    app.button(key='submit').click().run()
    assert not app.exception
    assert app.success[0].value == 'Resolved'
    app.radio(key='submission_mode').set_value('Follow-up to current ticket')
    app.text_area[0].input('What about a replacement?')
    app.button(key='submit').click().run()
    assert not app.exception
    assert app.success[0].value == 'Resolved'
    assert 'product.md' in app.session_state['ticket_history'][-1]['kb_sources']
    assert 'blender' in app.session_state['ticket_history'][-1]['complaint']
    app.button(key='reset_thread').click().run()
    app.text_area[0].input('Do you sell gift cards for 500 employees with custom branding?')
    app.button(key='submit').click().run()
    assert not app.exception
    assert app.warning[0].value == 'Escalated'
    rows = list(app.session_state['ticket_history'])
    assert len(rows) == 3
    assert 'blender' not in rows[-1]['complaint']
    assert rows[-1]['kb_sources'] == ''
    assert len(app.dataframe) == 1
    output = dict(mode='REAL OpenAI API through Streamlit AppTest', synthetic=True,
        assertions='Resolved product → context-aware Resolved follow-up → reset → Escalated unknown policy; CSV table present',
        tickets=rows, actual_agent_outputs=dict(app.session_state['agent_outputs']))
    (ROOT / 'evidence' / 'ui_apptest_results.json').write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
