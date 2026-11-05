import csv
import json
import pytest
from autogen_core import FunctionCall
from autogen_core.models import CreateResult, RequestUsage
from autogen_ext.models.replay import ReplayChatCompletionClient
from autogen_agentchat.agents import AssistantAgent


def tool_call(name):
    return CreateResult(finish_reason='function_calls', content=[FunctionCall(id=name, name=name, arguments='{}')], usage=RequestUsage(prompt_tokens=0, completion_tokens=0), cached=False)


def replay():
    return ReplayChatCompletionClient([
        json.dumps(dict(category='Shipping', urgency='Low', sentiment='Neutral', summary='Delivery question')),
        tool_call('search_kb'), 'Retrieved shipping.md.',
        json.dumps(dict(confidence=0.95, evidence=[dict(filename='shipping.md', quote='Orders arrive in 3-5 business days.') ])),
        tool_call('log_ticket'), 'Ticket logged.',
    ], model_info=dict(vision=False, function_calling=True, json_output=True, family='unknown', structured_output=True))


@pytest.mark.asyncio
async def test_four_real_agents_execute_in_order_and_log_canonical_state(tmp_path):
    import support
    assert hasattr(support, 'SupportTeam'), 'sequential team is missing'
    kb = tmp_path / 'kb'
    kb.mkdir()
    (kb / 'shipping.md').write_text('# Shipping\nOrders arrive in 3-5 business days.')
    client = replay()
    phases = []
    team = support.SupportTeam(client, kb_dir=kb, log_path=tmp_path / 'tickets.csv')
    assert len(team.agents) == 4
    assert all(isinstance(a, AssistantAgent) for a in team.agents)
    result = await team.process('Where is my order?', 'Synthetic', 'DEMO-1', on_event=lambda phase, text: phases.append(phase))
    assert list(dict.fromkeys(phases)) == ['query', 'knowledge', 'resolution', 'log']
    assert result['status'] == 'Resolved'
    assert result['kb_sources'] == 'shipping.md'
    assert '3-5 business days' in result['response']
    assert team.search_called and team.log_called
    rows = list(csv.DictReader((tmp_path / 'tickets.csv').open()))
    assert len(rows) == 1
    assert rows[0]['status'] == result['status']
    assert rows[0]['customer_name'] == 'Synthetic'
    await client.close()


@pytest.mark.asyncio
async def test_model_failure_is_bounded_escalated_and_logged_once(tmp_path):
    import support
    client = ReplayChatCompletionClient(['not valid JSON'], model_info=dict(vision=False, function_calling=True, json_output=True, family='unknown', structured_output=True))
    team = support.SupportTeam(client, log_path=tmp_path / 'tickets.csv', phase_timeout=0.5)
    events = []
    row = await team.process('Help with my order', on_event=lambda phase, text: events.append((phase, text)))
    assert row['status'] == 'Escalated'
    assert 'unavailable' in row['escalation_reason'].lower()
    assert list(dict.fromkeys(p for p, _ in events)) == ['query', 'knowledge', 'resolution', 'log']
    assert len(list(csv.DictReader((tmp_path / 'tickets.csv').open()))) == 1
    with pytest.raises(RuntimeError, match='fresh'):
        await team.process('Another complaint')
    await client.close()
