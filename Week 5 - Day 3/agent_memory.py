"""AutoGen memory seeded exclusively from fictional service catalog."""
import json
from pathlib import Path
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

async def build_service_memory():
    memory = ListMemory()
    catalog = json.loads(Path(__file__).with_name('service_catalog.json').read_text(encoding='utf-8'))
    for key, value in catalog.items():
        await memory.add(MemoryContent(
            content=f"Approved DEMO routing entry: {key} / {value['team']}. Scope: {value['scope']}. Next step: {value['next_step']}",
            mime_type=MemoryMimeType.TEXT,
        ))
    return memory

# Understand the Important Code
# ListMemory adds the fictional service catalog to specialist context.
# It is refreshed from the catalog at each app request and holds no employee history.
# Important Notes
# This is in-process reference memory, not persistent personal memory or vector RAG.
