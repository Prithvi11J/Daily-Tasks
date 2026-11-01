# Cybersecurity Support Center

**A cybersecurity service-routing web application built with Microsoft AutoGen and Streamlit.**

Employees describe a problem in everyday language. A Strategy Manager agent helps identify which cybersecurity team can assist, and specialist agents explain the next steps. If one message contains two separate requests, the application can route them separately.

> **Demonstration only:** All team ownership rules and service descriptions are fictional. This application is not connected to a company network. It does not open real tickets, create accounts, grant access or approve production privileges. Do not enter confidential data or real passwords.

## 1. What problem does this solve?

Employees may know what they need but not which team provides the service.

For example, an employee says:

> “My VPN is not connecting, and I need a new service account.”

The application should identify two separate issues:

| Employee needs help with | Team recommended |
|---|---|
| VPN connectivity | Network Security |
| New service account | Identity & Access Management (IAM) |

It displays a separate explanation and next step for each request. No ticket is created automatically.

## 2. Main features

- **Seven AI agents:** A Strategy Manager and six security specialists.
- **Multi-request routing:** One message may involve more than one team.
- **AutoGen Swarm handoffs:** The manager passes a request to a specialist.
- **Streamlit dashboard:** A support form, result cards, clear/new request button and service directory.
- **Agent activity:** An expandable view of the routing and handoff steps.
- **Demo PAM approval:** A human reviewer can mark a privileged-access request approved or rejected in the local demo database.
- **Service memory:** AutoGen `ListMemory` supplies fictional team responsibilities to the agents.
- **State checkpoints:** Optional JSON snapshots save AutoGen team state for testing.
- **Validation:** A separate script can test memory lookup and continuing from a saved checkpoint.

## 3. How the application works

### Simple workflow

```text
Employee types a question in Streamlit
                 |
                 v
Strategy planner identifies separate requests
                 |
                 v
Strategy Manager routes each request
                 |
       +---------+---------+
       |                   |
       v                   v
 Network Security         IAM            (example)
       |                   |
       +---------+---------+
                 |
                 v
  Streamlit displays both responses
                 |
                 v
If PAM is requested: create a PENDING demo approval
                 |
                 v
Human reviewer can APPROVE or REJECT the demo record
```

**Important:** Each detected service request runs through its own AutoGen Swarm workflow. The individual workflows run sequentially; this is not one giant group conversation involving every agent at once.

### Agent responsibilities

| Agent | Example requests |
|---|---|
| **Strategy Manager** | Decides which specialist should handle a request |
| **IAM** | Service accounts, application access, MFA, SSO, PAM |
| **Cloud Security** | Cloud security configurations, cloud risks and reviews |
| **Network Security** | VPN, firewall and network connectivity |
| **Endpoint Security** | Device security, lost or compromised laptops |
| **Data Security** | Sensitive information, data classification, DLP |
| **Product Security** | Application vulnerabilities and product security reviews |

**Note:** Laptop *replacement or procurement* may belong to IT Service Desk or asset management in a real organization. The demo should not assume a replacement means a security incident.

## 4. Project folder structure

Keep the Python files in the **same main folder** because the imports use their filenames directly.

```text
Cyber Support Agent/
|
|-- app.py                      Main Streamlit application and user interface
|-- agents.py                   Strategy planner, manager and specialist agents
|-- workflow.py                 AutoGen Swarm and handoff configuration
|-- service_catalog.json       Fictional services and team responsibilities
|-- agent_memory.py             Loads the service catalog into ListMemory
|-- state_store.py              Saves and reads AutoGen JSON checkpoints
|-- approval_store.py           Stores demo PAM decisions in SQLite
|-- validate_state_memory.py    Tests memory and saved-state continuation
|-- main.py                     Optional terminal-based test
|-- README.md                   This guide
|-- .gitignore                  Excludes private and generated files
|
|-- .env                        API key and local reviewer passcode (do not upload)
|-- venv/                       Python environment (do not upload)
|
`-- runtime_data/               Generated locally (do not upload)
    |-- pam_approvals.sqlite3    Demo approval database
    `-- team_states/            Optional saved team-state JSON files
```

### What is inside each important file?

- **`app.py`** — The page employees see. It accepts requests, calls the agents, displays the right teams, shows activity and hosts the demo reviewer controls.
- **`agents.py`** — Defines the Strategy planner, Strategy Manager and six specialist agents. It also sets their roles and instructions.
- **`workflow.py`** — Builds the AutoGen Swarm and controls when the routing conversation stops.
- **`service_catalog.json`** — Fictional reference information describing team responsibilities. Edit this file to maintain demo service definitions.
- **`agent_memory.py`** — Loads the catalog into AutoGen `ListMemory` so agents receive relevant service reference information.
- **`approval_store.py`** — Creates and updates local PAM review records using SQLite.
- **`state_store.py`** — Stores and reads AutoGen team-state checkpoints as JSON.
- **`validate_state_memory.py`** — A test script for memory lookup and loading a saved team state.
- **`main.py`** — Runs a simpler version from the terminal to test specialist handoffs.

## 5. Technology used

| Technology | Why we used it |
|---|---|
| Python 3.12 | Runs the application |
| Microsoft AutoGen | Creates agents and handles specialist handoffs |
| OpenAI `gpt-4o-mini` | Powers the agents' language understanding and responses |
| Streamlit | Creates the interactive web page |
| `ListMemory` | Provides reusable fictional service information |
| SQLite | Stores simulated PAM approval decisions |
| JSON | Stores the service catalog and optional state checkpoints |
| `python-dotenv` | Loads credentials from `.env` |

## 6. How to run the project (Windows CMD)

Open **Command Prompt** in the project directory:

```cmd
cd "C:\Users\prith\Cyber Support Agent"
```

If you have not yet created a virtual environment:

```cmd
py -3.12 -m venv venv
```

Activate it:

```cmd
venv\Scripts\activate
```

Install the Python packages:

```cmd
python -m pip install -U autogen-agentchat "autogen-ext[openai]" streamlit python-dotenv
```

Create a `.env` file in the main project folder:

```dotenv
OPENAI_API_KEY=your_openai_key_here
DEMO_REVIEWER_PASSCODE=your_private_demo_passcode
```

Use a unique **demo** passcode, not a workplace password. Never upload `.env` to GitHub.

Start the web app:

```cmd
python -m streamlit run app.py
```

Open **http://localhost:8501** if the browser does not open automatically. Press **Ctrl+C** in CMD when you want to stop it.

## 7. Test the application

| Question to enter | What you should expect |
|---|---|
| “My VPN is not connecting.” | Network Security |
| “I need a new service account.” | IAM |
| “Please review our cloud security configuration.” | Cloud Security |
| “My company laptop was stolen.” | Endpoint Security |
| “Our application has a critical vulnerability.” | Product Security |
| “Sensitive data was shared incorrectly.” | Data Security |
| “My VPN is broken and I need a new service account.” | **Two** responses: Network Security and IAM |
| “I need PAM administrator access.” | IAM guidance and a **PENDING** demo approval |

### Test the PAM reviewer

1. Submit a PAM/privileged-access request.
2. Open the reviewer panel in Streamlit.
3. Enter your **demo** reviewer passcode.
4. Open the pending request and select **Approve** or **Reject**.
5. Confirm the status changes. **No real access is granted.**

## 8. AutoGen concepts explained

### Agent, tool and handoff

An **agent** is an AI component assigned a specific responsibility. A **tool** is a function an agent can use. A **handoff** transfers control from one agent to another.

For example, the Strategy Manager identifies a VPN request and hands it to the Network Security agent. The agent activity view shows that handoff.

### State

**State = the team's saved execution context.** AutoGen supports `team.save_state()` and `team.load_state()`. This project can save JSON checkpoints, and the validation script demonstrates loading one into a new team.

A checkpoint does **not** mean the Streamlit conversation will automatically resume. A restored team may still have a specialist as its active agent, so unrelated new questions should start with the Strategy Manager again.

### Memory

**Memory = reference information supplied to agents.** Here, AutoGen `ListMemory` holds fictional service guidance from `service_catalog.json`.

This is **not RAG**: there is no embedding model or vector database in this project.

### Human-in-the-loop (HITL)

Sensitive PAM requests require a human decision. The reviewer can record **APPROVED** or **REJECTED**, but this changes only a local database record. This is an **application-level approval gate**, not a live AutoGen workflow paused and resumed around the reviewer.

### Observing agents

The **Agent activity** panel shows the Strategy Manager's handoffs and specialist responses. It helps developers understand which agent processed each request. This is simple observability, not a full enterprise tracing system.

### MCP

**MCP is not implemented in this version.** It could later connect approved internal service catalogs or tools, but it is not necessary for this standalone demonstration.

## 9. Limits and safety

This is a working **prototype**, not a deployed corporate service. In particular:

- Team responsibilities are fictional and might not match real organizational ownership.
- LLM-based routing can make mistakes; ambiguous requests should be clarified.
- There is no internal knowledge-base RAG, ticketing integration or real access provisioning.
- The reviewer passcode is only for local demonstration; enterprise access needs SSO, RBAC and audit trails.
- Saved state or database records could contain entered questions, so never test with real confidential information.

## 10. What to upload to GitHub

**Include:** All project Python files, `service_catalog.json`, `README.md` and `.gitignore`.

**Exclude:** `.env`, `venv/`, `runtime_data/`, `__pycache__/`, generated databases and saved state files.

Verify in CMD:

```cmd
git status
```

## Project outcome

This project demonstrates how to develop a **seven-agent AutoGen service-routing application** with a Streamlit dashboard, multi-intent requests, specialist handoffs, simulated PAM approval, service reference memory, optional saved team state and an observable activity trail.
