# Customer Support Agents — AutoGen assignment

A local Streamlit app with **four real `autogen_agentchat.agents.AssistantAgent` instances**, real OpenAI `gpt-4o-mini` calls, local policy retrieval, deterministic escalation, and an idempotent CSV ticket log. All included policies, customer identities, and evidence complaints are **fictional synthetic coursework data**. This is not connected to a retailer, order system, payment gateway, or staffed support queue.

## Setup: Linux / macOS

Tested on Linux with **Python 3.14.9**, AutoGen 0.7.5, Streamlit 1.66.1; exact direct/transitive versions are in `requirements.txt`. Windows commands below are provided but Windows itself was not exercised.

```bash
cd customer-support-agents
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python save_api_key.py
python -m streamlit run app.py --server.address 127.0.0.1
```

`save_api_key.py` prompts without echo and refuses to overwrite an existing `.env`. Alternatively copy `.env.example` to `.env`, then edit it locally. Never send the key in chat, commit it, or include it in a ZIP. The key is read from the environment first, then the `.env` adjacent to `support.py`; only `OPENAI_API_KEY` is required. Network calls use ordinary certificate verification—no insecure TLS overrides.

On Debian/Ubuntu, if system Python reports that ensurepip is missing, install its matching `python3-venv` package yourself or use a Python installation with venv support. No global package changes are required by this project.

## Setup: Windows CMD

Use a Python 3.14 installation:

```bat
cd customer-support-agents
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python save_api_key.py
python -m streamlit run app.py --server.address 127.0.0.1
```

Open `http://127.0.0.1:8501` locally. Stop with **Ctrl+C**. This submission does not deploy anything. `.streamlit/config.toml` binds to loopback by default; the explicit flag above also protects launches from a different working directory. Do not bind to `0.0.0.0` or expose this demo publicly: it has no authentication.

## Files and architecture

```text
app.py                    single UI entrypoint
support.py                typed schemas, four agents, orchestration, tools, safety gate
knowledge_base/*.md       four fictional policies; .txt additions supported
logs/tickets.csv          automatically created on first accepted submission (excluded)
save_api_key.py           existing secure interactive configuration helper
requirements.txt          pinned installed dependencies
.streamlit/config.toml    local-only server defaults
.env.example              empty credential template; NOT a real secret
pytest.ini, tests/        deterministic and explicitly opt-in paid live tests
evidence/                 sanitized SYNTHETIC real-execution results
```

Execution is deliberately sequential, not a potentially looping group chat:

1. **Query** returns a validated Pydantic `category`, `urgency`, `sentiment`, and summary.
2. **Knowledge** calls the actual no-argument `search_kb` tool. The tool owns its query and filesystem scope and returns local passages with filenames.
3. **Resolution** chooses exact policy quotes and confidence. The orchestrator verifies each filename and exact substring. The customer reply uses **only verified verbatim policy excerpts**, not arbitrary generated promises.
4. **Log** calls actual no-argument `log_ticket`. The tool writes the orchestrator's canonical fields, not LLM-authored CSV content.

High urgency, Angry/Very Angry sentiment, explicit legal/fraud/payment-dispute/severe-anger patterns, no documents, confidence below **0.75**, invalid citations, and earlier service errors deterministically force **Escalated**. Matching policy advice with valid evidence can be **Resolved**; that means the information request is answered, **not** that money was refunded or a physical replacement was shipped. Escalation is a local flag only, not a claim that a human was contacted.

Four fresh agent conversations and a fresh API client are created per submission. Each phase has a 35-second deadline and at most 12 streamed events; tool agents have one tool iteration. HTTP calls have a 25-second timeout and no automatic retries. Total agent work is bounded to 140 seconds (plus small local I/O/client-close overhead). Tools are idempotent, and final success is not reported until the log write succeeds. When an API/tool agent fails, a safe escalated record is attempted; if the log agent cannot run, the same canonical log tool is invoked directly and explicitly marked as a fallback in agent outputs. Disk/configuration failures display a generic safe error rather than raw exceptions or credentials.

CSV columns are exactly:

```text
ticket_id,timestamp,customer_name,order_id,complaint,category,urgency,sentiment,kb_sources,response,status,escalation_reason
```

Writes are thread-safe within the single Streamlit process and idempotent by ticket ID, with CSV quoting and spreadsheet-formula escaping. Do not run multiple independent writer processes against the same CSV; a production multi-worker system needs a database/transactional locking. Timestamps use UTC.

## Retrieval, new policies, and portable paths

Place a UTF-8 `.md` or `.txt` document directly in **`knowledge_base/`**. Use a descriptive heading, explicit policy facts, and exact product/FAQ IDs where relevant. The next request discovers it automatically: **no index build and no code edit**. Only trusted local administrators should edit policy files. Symlink files are ignored. Each retrieved passage is bounded to 10,000 characters and at most four documents are returned. Very large corpora need a proper retrieval index, which is intentionally out of scope.

Retrieval uses Unicode-aware lexical tokens, simple English plural normalization, exact hyphenated identifiers (e.g. `ZX-900`, `POL-77`), and category weighting. It is not semantic-only retrieval or an embedding placeholder. It can miss paraphrases and should escalate rather than invent a policy. English agent classification and keyword escalation rules are a demo baseline, not a multilingual guarantee.

Optional environment/`.env` settings:

```dotenv
KB_DIRECTORY=knowledge_base
TICKET_LOG_PATH=logs/tickets.csv
```

Relative paths resolve against **`Path(__file__).resolve().parent`**, never the caller's working directory. Absolute paths are also accepted for administrator configuration. Case matters on Linux; use the exact names above. Missing/empty KBs safely return no documents. A fresh checkout requires no ignored index or CSV; log directories/files are automatically created.

## Follow-ups and session isolation

The UI retains ticket history and agent outputs in `st.session_state`. Select **Follow-up to current ticket** to include up to four previous customer messages from the current thread. A follow-up creates a **new child ticket ID and exactly one new CSV row**, with the parent ID and previous context explicitly included in the complaint field. The parent is not overwritten. This keeps immutable audit rows while giving new agents the relevant conversation context.

**New ticket** does not include the previous thread. **Start new conversation** clears the active context and outputs, while retaining this session's history. Separate browser sessions do not share conversation state. The UI's table/download contains only the current session's rows, not other sessions' local CSV records. The persisted local CSV may contain all submissions and is private; it is deliberately excluded from the submission ZIP. Session UI history is not restored after browser/server restart. Do not submit payment card details, passwords, or actual personal data.

## Repeatable tests

Offline, deterministic helpers + real AutoGen agents backed by an explicitly labeled replay client + Streamlit AppTest (no paid API calls):

```bash
python -m pytest tests -q
```

Paid opt-in **real OpenAI API**, synthetic inputs only:

Linux/macOS:

```bash
RUN_LIVE_TESTS=1 python -m pytest tests -q
```

Windows CMD:

```bat
set RUN_LIVE_TESTS=1
python -m pytest tests -q
set RUN_LIVE_TESTS=
```

The live suite evaluates the six assignment complaints plus fraud and standard-delivery cases; it checks expected category/status, actual tool events/order, returned source filenames, policy facts (30-day returns, 5–10-business-day refunds, 3–5-business-day shipping, 7-day damaged-product reporting), no unsupported action promises, and exactly one log row per ticket. It computes metrics and persists `evidence/results.json`, detailed `live_results.json`, and an explicitly synthetic CSV. A real API AppTest also submits a broken-product complaint, a context-aware replacement follow-up, resets, and submits an unknown gift-card request. No model judge or printed-only “test” substitutes for assertions.

Latest verified execution: **20 tests passed**, including all **8/8 evaluated live complaint cases**, plus the real API UI/follow-up test. A separate fresh environment installed only `requirements.txt` from the extracted submission ZIP: **11 passed, 9 opt-in live tests skipped**, and `pip check` returned `No broken requirements found.` No `.env`, prebuilt CSV, or index was present in that checkout. See `evidence/clean_install.json` and `evidence/verification.txt` for actual clean-install and loopback-health evidence. `evidence/results.json` contains computed pass/fail and source metrics; `evidence/pytest_full.txt` is actual pytest output. Third-party AutoGen/Python 3.14 deprecation warnings and OpenAI/Pydantic parsed-value serialization warnings are visible in this output; they did not prevent successful typed outputs, tool calls, or persisted tickets. Offline tests deliberately skip the nine opt-in live test items.

## Demonstration / screenshots

Run the UI locally, submit the delayed-order complaint, and capture the **Resolved** badge, policy citations, and four agent panels. Start a new conversation, submit the triple-charge/legal-threat complaint, and capture **Escalated** and the reason. Capture the session CSV table/download. Only use synthetic identities in screenshots. **No screenshots are claimed in this submission**: actual Streamlit AppTest UI evidence is in `evidence/ui_apptest_results.json`; it is a structured test artifact, not a rendered image.

## Limits / production work intentionally excluded

No real refund/order/account integrations, human notification service, authentication, durable chat restoration, OCR/vector database, or deployment. Confidence is model-reported but independently gated by exact source evidence and deterministic risk rules; keyword rules are conservative and are not exhaustive fraud/legal detection. Extractive replies favor verifiability over conversational polish. These limitations are explicit, not hidden behind fabricated live data.
