# src/rag_agent_framework/agents/crew.py -- Crew Assembly -- The entire agentic system defintions

from crewai import Crew, Process
from .research_agents import document_researcher, general_researcher, report_writer
from .tasks import document_research_task, web_research_task, writer_task

# Assemble the new sequential crew
agent_crew = Crew(
    agents = [document_researcher, general_researcher, report_writer],
    tasks = [document_research_task, web_research_task, writer_task],
    process = Process.sequential,
    verbose = True
)

def get_crew():
    """Returns the configured agent crew"""
    return agent_crew