"""Validate AutoGen service memory and checkpoint continuation (fictional data only)."""
import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console
from workflow import create_team
from agent_memory import build_service_memory
from state_store import load_team_state

load_dotenv()
STATE_DIR = Path(__file__).resolve().parent / 'runtime_data' / 'team_states'

async def main():
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError('Set OPENAI_API_KEY in .env first.')

    # Check that the fictional service catalog was loaded as AutoGen memory.
    memory = await build_service_memory()
    memory_results = await memory.query("cybersecurity service routing")
    catalog = json.loads(Path(__file__).with_name('service_catalog.json').read_text(encoding='utf-8'))
    memory_text = "\n".join(str(item.content) for item in memory_results.results).lower()
    print('\n=== MEMORY CHECK ===')
    for agent, entry in catalog.items():
        team = entry['team']
        present = team.lower() in memory_text
        print(f'{agent}: {"LOADED" if present else "NOT FOUND"} — {team}')
        if not present:
            raise RuntimeError(f'Missing memory entry for {agent}')
    print('Note: ListMemory is a reference list, not vector similarity search.')

    # Find an actual snapshot created when the Stage 4 checkbox was enabled.
    checkpoints = sorted(STATE_DIR.glob('*.json'), key=lambda f: f.stat().st_mtime)
    if not checkpoints:
        print('\nNo checkpoint found. Enable Save AutoGen team state in Streamlit,')
        print('run a fictional support request, then execute this script again.')
        return

    checkpoint = checkpoints[-1]
    print(f'\n=== STATE RESTORE ===\nLoading: {checkpoint.name}')
    saved_state = load_team_state(str(checkpoint))
    print('Saved state fields:', ', '.join(saved_state.keys()))
    model_client = OpenAIChatCompletionClient(model='gpt-4o-mini', temperature=0)
    try:
        # This is a newly constructed team, not the instance that saved state.
        restored_team = create_team(model_client, service_memory=memory)
        await restored_team.load_state(saved_state)
        print('Successfully called load_state() on a fresh AutoGen Swarm.')
        print('\n=== CONTINUATION TEST ===')
        print('Sending follow-up into the restored team (no real service action).')
        result = await Console(restored_team.run_stream(task=(
            'For the support request discussed earlier, briefly explain which '
            'fictional specialist team is responsible and what details the employee '
            'should include when requesting help. Do not invent prior facts. '
            'Do not create tickets, approvals, or access changes.'
        )))
        print('\nContinuation completed. Messages:', len(result.messages))
        print('Check the messages above for the specialist response and any handoff.')
    finally:
        await model_client.close()

if __name__ == '__main__':
    asyncio.run(main())

# Understand the Important Code
# memory.query() returns the fictional catalog entries stored by ListMemory.
# load_team_state() reads a checkpoint saved by the Stage 4 Streamlit app.
# restored_team.load_state() restores that checkpoint into a NEW Swarm instance.
# restored_team.run_stream() attempts to continue from the restored context.

# Important Notes
# Use fictional questions only; checkpoints can contain conversation text.
# This demonstrates explicit restoration, not automatic PAM workflow resumption.
# The simulated PAM approval database remains separate from AutoGen team state.
