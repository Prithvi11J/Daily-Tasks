import json
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent

CATALOG = json.loads(Path(__file__).with_name('service_catalog.json').read_text(encoding='utf-8'))
ROUTES = {
    'iam': 'Accounts, service accounts, access, MFA, SSO and PAM',
    'cloud_sec': 'Cloud security posture, risky cloud configurations',
    'network_sec': 'VPN, firewalls and network connectivity',
    'endpoint_sec': 'Endpoint protection, managed devices, lost or stolen devices; hardware procurement may belong to IT',
    'data_sec': 'Sensitive data, classification, DLP and data exposure',
    'prod_sec': 'Application vulnerabilities, secure coding and product security reviews',
}


def create_planner(model_client):
    """Plan distinct user requests before initiating separate specialist handoffs."""
    descriptions = '\n'.join(f'{key}: {value}' for key, value in ROUTES.items())
    return AssistantAgent(
        name='strategy_intent_planner', model_client=model_client,
        system_message=(
            'You are a Strategy Team cybersecurity service-routing planner for a FICTIONAL demo. '
            'Split the employee message into distinct actionable requests, including requests joined by AND. '
            'Return ONLY a JSON object with key "requests", whose value is an array of objects '
            'containing "request" (one specific request) and "team" (one exact team key). '
            'Allowed teams:\n' + descriptions + '\n'
            'A single employee message may require multiple different teams. '
            'A request for a REPLACEMENT laptop is not evidence of theft, malware or compromise. '
            'Hardware replacement may actually be owned by IT Service Desk; route device-related '
            'requests to endpoint_sec for guidance about the correct owning service, not for an incident declaration. '
            'Service-account creation belongs to iam; PAM only when explicit privileged access is requested. '
            'Do not add requests that were not made. Use at most six requests. '
            'For questions outside these areas or with insufficient clarity, return {"requests":[]}.'
        ),
    )


def create_agents(model_client, service_memory=None):
    descriptions = '\n'.join(f'- {key}: {value}' for key, value in ROUTES.items())
    manager = AssistantAgent(
        name='strategy_manager', model_client=model_client,
        description='Strategy Team manager that transfers one scoped service request to a specialist.',
        handoffs=list(ROUTES),
        system_message=(
            'You are the Strategy Team routing manager for a FICTIONAL cybersecurity support demo. '
            'You receive ONE scoped employee request per run. Transfer it to exactly one specialist '
            'using the appropriate transfer tool; never answer for a specialist. '
            'Specialists:\n' + descriptions + '\n'
            'Use the team identified in the request if a routing hint is provided. '
            'Do not assume a laptop replacement means a lost device or security incident. '
            'Never request credentials or secrets. If genuinely unclear, briefly ask for clarification '
            'and finish with ROUTING_COMPLETE.'
        ),
    )
    specialists = []
    for name, entry in CATALOG.items():
        notes = (
            'For a requested replacement laptop, NEVER assume it is lost, stolen, infected, '
            'or compromised. Say device replacement may be owned by IT Service Desk / asset management '
            'and confirm ownership; only mention incident reporting if an incident is explicitly described.'
            if name == 'endpoint_sec' else ''
        )
        specialists.append(AssistantAgent(
            name=name, model_client=model_client, description=entry['scope'],
            memory=[service_memory] if service_memory is not None else [],
            system_message=(
                f'You are the {entry["team"]} specialist in a FICTIONAL service-routing demo. '
                f'Your scope: {entry["scope"]}. General guidance: {entry["next_step"]}. '
                'Address ONLY the scoped request, not other requests in the original message. '
                'Give exactly: Team, Why this team, Next step. '
                'Do not invent internal URLs, policies, contacts, approvals, or a security incident. '
                'Say when another department may own the service. '
                'For actual privileged/PAM access requests, state human approval is mandatory, '
                'and the demo application can record a pending human decision; no actual access is granted. Do not ask for secrets. '
                + notes + ' End with ROUTING_COMPLETE.'
            ),
        ))
    return [manager, *specialists]
