from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import Swarm
from agents import create_agents


def create_team(model_client, service_memory=None):
    agents = create_agents(model_client, service_memory=service_memory)
    stop = TextMentionTermination("ROUTING_COMPLETE") | MaxMessageTermination(max_messages=12)
    return Swarm(participants=agents, termination_condition=stop)
