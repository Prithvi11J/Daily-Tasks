import csv
import pytest
from test_team import replay


@pytest.mark.asyncio
async def test_public_runner_creates_fresh_team_and_closes_client(tmp_path, monkeypatch):
    import support
    assert hasattr(support, 'run_ticket'), 'public runner is missing'
    clients = []
    def factory():
        client = replay()
        clients.append(client)
        return client
    monkeypatch.setattr(support, 'create_model_client', factory)
    kb = tmp_path / 'kb'
    kb.mkdir()
    (kb / 'shipping.md').write_text('Orders arrive in 3-5 business days.')
    first = await support.run_ticket('Where is my order?', log_path=tmp_path / 'tickets.csv', kb_dir=kb)
    second = await support.run_ticket('Where is my order?', log_path=tmp_path / 'tickets.csv', kb_dir=kb)
    assert first['ticket_id'] != second['ticket_id']
    assert len(clients) == 2
    assert len(list(csv.DictReader((tmp_path / 'tickets.csv').open()))) == 2
