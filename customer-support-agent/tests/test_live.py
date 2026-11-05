"""Opt-in real API acceptance tests. All complaints and identities are synthetic."""
import asyncio
import csv
import json
import os
from pathlib import Path
import pytest
from support import ROOT, run_ticket

CASES = [
    ('shipping_delay', 'Where is my order? It was supposed to arrive yesterday.', ['Shipping'], 'Resolved'),
    ('refund', 'I want to return the shoes I bought last week. How do I get a refund?', ['Refund'], 'Resolved'),
    ('account', "I forgot my password and can't log in.", ['Account'], 'Resolved'),
    ('broken_product', 'The blender I received is broken. Can I get a replacement?', ['Product', 'Refund'], 'Resolved'),
    ('billing_legal', "You charged my card three times! Fix this now or I'm contacting my bank and a lawyer.", ['Billing'], 'Escalated'),
    ('unknown_policy', 'Do you sell gift cards for a company of 500 employees with custom branding?', ['Other'], 'Escalated'),
    ('fraud', 'There is an unauthorized purchase on my account. This is fraud.', ['Billing', 'Account'], 'Escalated'),
    ('delivery_timeline', 'How long does standard delivery normally take?', ['Shipping'], 'Resolved'),
]

pytestmark = [pytest.mark.live, pytest.mark.skipif(os.getenv('RUN_LIVE_TESTS') != '1', reason='Set RUN_LIVE_TESTS=1 to allow paid real OpenAI calls')]


@pytest.fixture(scope='module')
def live_paths():
    folder = ROOT / 'evidence'
    folder.mkdir(exist_ok=True)
    (folder / 'live_results.json').write_text('[]', encoding='utf-8')
    path = folder / 'synthetic_live_tickets.csv'
    path.unlink(missing_ok=True)
    return folder, path


@pytest.mark.parametrize('name,complaint,categories,status', CASES, ids=[c[0] for c in CASES])
def test_live_scenario(name, complaint, categories, status, live_paths):
    folder, log_path = live_paths
    events = []
    row = asyncio.run(run_ticket(complaint, 'SYNTHETIC TEST CUSTOMER', 'DEMO-ONLY', log_path=log_path,
        on_event=lambda phase, text: events.append(dict(phase=phase, output=text))))
    expected_source = {'shipping_delay': 'shipping.md', 'refund': 'refund.md', 'account': 'account.md', 'broken_product': 'product.md', 'delivery_timeline': 'shipping.md'}.get(name)
    facts = {'shipping_delay': ['tracking', 'order number'], 'refund': ['30 days', '5-10 business days'], 'account': ['Forgot password', 'reset link'], 'broken_product': ['7 days', 'photos', 'replacement'], 'delivery_timeline': ['3-5 business days']}.get(name, ['human support', 'no refund'])
    checks = dict(status=row['status'] == status, category=row['category'] in categories,
        expected_source=not expected_source or expected_source in row['kb_sources'],
        factual_answer=all(fact.lower() in row['response'].lower() for fact in facts),
        agent_order=list(dict.fromkeys(e['phase'] for e in events)) == ['query', 'knowledge', 'resolution', 'log'],
        actual_search_tool=any('search_kb' in e['output'] for e in events if e['phase'] == 'knowledge'),
        actual_log_tool=any('log_ticket' in e['output'] for e in events if e['phase'] == 'log'),
        no_fallback=not any('unavailable' in e['output'].lower() for e in events),
        no_unsupported_promises=not any(text in row['response'].lower() for text in ['i have refunded', 'replacement has been sent', 'your order is at']))
    if name == 'unknown_policy':
        checks['empty_retrieval'] = not row['kb_sources']
    if name == 'billing_legal':
        checks['high_angry'] = row['urgency'] == 'High' and row['sentiment'] in ['Angry', 'Very Angry']
    saved = list(csv.DictReader(log_path.open(encoding='utf-8', newline='')))
    checks['exactly_one_log_row'] = sum(old['ticket_id'] == row['ticket_id'] for old in saved) == 1
    record = dict(case=name, checks=checks, passed=all(checks.values()), synthetic=True, mode='REAL OpenAI gpt-4o-mini API execution',
        expected_status=status, expected_categories=categories, result=row, agent_events=events)
    path = folder / 'live_results.json'
    records = json.loads(path.read_text(encoding='utf-8'))
    records.append(record)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')
    passed = sum(item['passed'] for item in records)
    summary = dict(synthetic=True, model='gpt-4o-mini', evaluated=len(records), passed=passed,
        failed=len(records) - passed, pass_rate=passed / len(records),
        retrieval_source_accuracy=sum(item['checks']['expected_source'] for item in records) / len(records), cases=records)
    (folder / 'results.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    assert all(checks.values()), checks
    assert row['status'] == status, row['escalation_reason']
    assert row['category'] in categories
    assert list(dict.fromkeys(e['phase'] for e in events)) == ['query', 'knowledge', 'resolution', 'log']
    assert any('search_kb' in e['output'] for e in events if e['phase'] == 'knowledge')
    assert any('log_ticket' in e['output'] for e in events if e['phase'] == 'log')
    assert not any('unavailable' in e['output'].lower() for e in events)
    rows = list(csv.DictReader(log_path.open(encoding='utf-8', newline='')))
    assert sum(old['ticket_id'] == row['ticket_id'] for old in rows) == 1
    if name == 'billing_legal':
        assert row['urgency'] == 'High'
        assert row['sentiment'] in ['Angry', 'Very Angry']
    if name == 'unknown_policy':
        assert not row['kb_sources']
        assert 'No matching policy' in row['escalation_reason']
