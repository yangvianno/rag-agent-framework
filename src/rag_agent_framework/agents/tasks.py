# src/rag_agent_framework/agents/tasks.py -- Agent Task Definitions

from crewai import Task
from .research_agents import document_researcher, general_researcher

document_researcher_task = Task(
    description = (
        "Investigate the following topic: '{topic}'. "
        "You must use the 'Document Knowledge Base Tool' to find relevant information within the provided documents."
    ),
    expected_output = "A detailed answer based only on the information found in the documents. Cite the source of your information.",
    agent = document_researcher
)

general_researcher_task = Task(
    description = (
        "Research the following topic on the web: '{topic}'. "
        "Specifically, find supplemental information that is not available in the private documents."
    ),
    expected_output = "A summary of the most relevant, up-to-date information from your web search.",
    agent = general_researcher
)