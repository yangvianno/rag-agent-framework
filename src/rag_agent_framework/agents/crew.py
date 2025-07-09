# src/rag_agent_framework/agents/crew.py -- Crew Assembly -- The entire agentic system defintions
from crewai import Crew, Process
from .research_agents import document_researcher, general_researcher
from .tasks import document_researcher_task, general_researcher_task

# Define the crew
agent_crew = Crew(
    agents = [document_researcher, general_researcher],
    tasks = [document_researcher_task, general_researcher_task],
    process = Process.sequential,   # Tells the crew to execute the tasks one by one, in order.
                                    # CrewAI will automatically pass the OUTPUT of one task as CONTEXT to the next.
    verbose = False                     # Prints more granular details, useful for understanding how agents are reasoning, which tools are being called, etc
)

def get_crew():
    """Returns the configured agent crew"""
    return agent_crew