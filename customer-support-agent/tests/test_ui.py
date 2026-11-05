from pathlib import Path
from streamlit.testing.v1 import AppTest
from support import ROOT


def test_ui_renders_form_and_rejects_blank_submission(tmp_path, monkeypatch):
    assert (ROOT / 'app.py').is_file(), 'Streamlit entrypoint is missing'
    monkeypatch.setenv('TICKET_LOG_PATH', str(tmp_path / 'tickets.csv'))
    app = AppTest.from_file(str(ROOT / 'app.py')).run()
    assert not app.exception
    assert app.title[0].value == 'Customer Support Agents'
    assert len(app.text_input) == 2
    app.button(key='submit').click().run()
    assert app.error
    assert not app.exception


def test_ui_runs_agents_retains_followup_and_reset_isolates_new_ticket(tmp_path, monkeypatch):
    import support
    from uuid import uuid4
    path = tmp_path / 'tickets.csv'
    monkeypatch.setenv('TICKET_LOG_PATH', str(path))
    inputs = []
    async def fake_runner(complaint, customer_name, order_id, *, on_event):
        # Explicitly a deterministic UI-boundary fixture, NOT live API evidence.
        inputs.append(complaint)
        for phase in ['query', 'knowledge', 'resolution', 'log']:
            on_event(phase, 'Deterministic UI test output')
        row = {key: '' for key in support.LOG_COLUMNS}
        row.update(ticket_id=str(uuid4()), complaint=complaint, customer_name=customer_name,
            order_id=order_id, response='Synthetic UI fixture reply', status='Resolved', category='Product')
        support.log_row(row, path)
        return row
    monkeypatch.setattr(support, 'run_ticket', fake_runner)
    app = AppTest.from_file(str(ROOT / 'app.py')).run()
    app.text_input[0].input('Synthetic UI customer')
    app.text_area[0].input('The blender is broken.')
    app.button(key='submit').click().run()
    assert not app.exception
    assert app.success[0].value == 'Resolved'
    assert len(app.dataframe) >= 1
    assert len(app.session_state['ticket_history']) == 1
    app.radio(key='submission_mode').set_value('Follow-up to current ticket')
    app.text_area[0].input('What about a replacement?')
    app.button(key='submit').click().run()
    assert 'The blender is broken.' in inputs[1]
    assert 'What about a replacement?' in inputs[1]
    assert len(app.session_state['ticket_history']) == 2
    app.button(key='reset_thread').click().run()
    app.text_area[0].input('How long does delivery take?')
    app.button(key='submit').click().run()
    assert inputs[2] == 'How long does delivery take?'
    assert not app.exception
