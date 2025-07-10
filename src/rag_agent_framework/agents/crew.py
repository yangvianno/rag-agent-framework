# src/rag_agent_framework/agents/crew.py -- Crew Assembly -- The entire agentic system defintions
from crewai import Crew, Process
from .research_agents import document_researcher, general_researcher, manager_agent
from .tasks import document_researcher_task, general_researcher_task, manager_task

# Define the crew with hierarchical process
agent_crew = Crew(
    agents = [manager_agent, document_researcher, general_researcher],
    tasks = [manager_task, document_researcher_task, general_researcher_task],
    process = Process.hierarchical,
    manager_llm = manager_agent.llm,    # Specify the manager agent
    verbose = True                      # Prints more granular details, useful for understanding how agents are reasoning, which tools are being called, etc
)

def get_crew():
    """Returns the configured agent crew"""
    return agent_crew