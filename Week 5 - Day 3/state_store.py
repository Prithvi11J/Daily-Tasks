"""Save demo AutoGen team state locally, only when opted in."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

STATE_DIR = Path(__file__).with_name('runtime_data') / 'team_states'

def save_team_state(team_state: dict) -> str:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    file = STATE_DIR / f'{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_{uuid4().hex[:8]}.json'
    file.write_text(json.dumps(team_state, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(file)

def load_team_state(path: str) -> dict:
    target = Path(path).resolve()
    if target.parent != STATE_DIR.resolve():
        raise ValueError('Only locally saved demo team states can be opened.')
    return json.loads(target.read_text(encoding='utf-8'))

# Understand the Important Code
# AutoGen team.save_state() returns a dictionary; this module persists it.
# load_team_state() reads it back for a compatible team.load_state() call.
# Important Notes
# State contains conversation contents. Do not store real employee or company secrets.
