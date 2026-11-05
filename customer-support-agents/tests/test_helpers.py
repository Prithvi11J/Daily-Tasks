from pathlib import Path
import importlib


def test_retrieval_returns_local_passage_and_unknown_is_empty(tmp_path):
    spec = importlib.util.find_spec('support')
    assert spec is not None, 'support module is missing'
    from support import search_documents
    (tmp_path / 'shipping.md').write_text('# Shipping\nOrders arrive in 3-5 business days.')
    assert search_documents('Shipping', tmp_path)[0]['filename'] == 'shipping.md'
    assert search_documents('Other', tmp_path) == []
    assert search_documents('Shipping', tmp_path / 'missing') == []


def test_escalation_cannot_be_overridden_by_model():
    import support
    assert hasattr(support, 'escalation_reasons'), 'safety boundary is missing'
    base = dict(urgency='Low', sentiment='Neutral')
    docs = [{'filename': 'shipping.md', 'passage': 'Shipping policy'}]
    for text in ['My lawyer will contact you', 'Unauthorized purchase', 'I dispute this payment', 'You charged my card three times!', 'This is fraud', 'I am furious']:
        assert support.escalation_reasons(text, base, docs, 1.0)
    assert support.escalation_reasons('hi', dict(urgency='High', sentiment='Neutral'), docs, 1)
    assert support.escalation_reasons('hi', dict(urgency='Low', sentiment='Very Angry'), docs, 1)
    assert support.escalation_reasons('hi', base, [], 1)
    assert support.escalation_reasons('hi', base, docs, 0.2)
    assert support.escalation_reasons('hi', base, docs, float('nan'))
    assert not support.escalation_reasons('Where is my order?', base, docs, 0.9)


def test_ticket_logging_is_idempotent_and_csv_safe(tmp_path):
    import support
    import csv
    assert hasattr(support, 'log_row'), 'CSV writer is missing'
    path = tmp_path / 'logs' / 'tickets.csv'
    row = {key: '' for key in support.LOG_COLUMNS}
    row.update(ticket_id='ticket-1', customer_name='=HYPERLINK("bad")', complaint='line one,\nline two', status='Escalated')
    assert support.log_row(row, path) == 'ticket-1'
    assert support.log_row(row, path) == 'ticket-1'
    rows = list(csv.DictReader(path.open()))
    assert len(rows) == 1
    assert rows[0]['customer_name'].startswith("'")
    assert rows[0]['complaint'] == row['complaint']
    assert list(rows[0]) == support.LOG_COLUMNS


def test_retrieval_rejects_unsupported_intent_even_if_misclassified(tmp_path):
    from support import search_documents
    (tmp_path / 'product.md').write_text('Broken products may be replaced.')
    assert search_documents('Product', tmp_path, complaint='Do you sell gift cards for 500 employees with custom branding?') == []
    assert search_documents('Product', tmp_path, complaint='My blender is broken')[0]['filename'] == 'product.md'


def test_new_text_policy_and_exact_product_code_are_discovered_without_code_changes(tmp_path):
    from support import search_documents
    assert search_documents('Other', tmp_path, complaint='FAQ ZX-900 policy POL-77') == []
    (tmp_path / 'special_faq.txt').write_text('# FAQ ZX-900\nPolicy POL-77: ZX-900 service requires a receipt.')
    matches = search_documents('Other', tmp_path, complaint='FAQ ZX-900 policy POL-77')
    assert matches[0]['filename'] == 'special_faq.txt'
    assert 'POL-77' in matches[0]['passage']


def test_default_paths_are_independent_of_cwd(tmp_path, monkeypatch):
    import support
    monkeypatch.chdir(tmp_path)
    assert support.search_documents('Shipping')[0]['filename'] == 'shipping.md'
    assert hasattr(support, 'project_path'), 'project-relative configurable paths are missing'
    assert support.project_path('knowledge_base') == support.ROOT / 'knowledge_base'
    assert support.project_path(tmp_path) == tmp_path
