# src/rag_agent_framework/agents/tasks.py -- Agent Task Definitions

from crewai import Task
from .research_agents import document_researcher, general_researcher

document_researcher_task = Task(
    description = (
        "Investigate the following topic: '{topic}'.\n"
        "Here is the context from past conversations, which might be relevant:\n"
        "{context}\n\n"
        "You MUST use the 'Document Knowledge Base Tool' to find the primary answer "
        "from within the provided documents. Use the context to better understand "
        "the user's intent and frame your search."
    ),
    expected_output = (
        "A detailed answer based only on the information found in the documents. "
        "Cite the source of your information. If past context was relevant, "
        "mention how it helped shape the answer."
    ),
    agent = document_researcher
)

general_researcher_task = Task(
    description = (
        "Research the following topic on the web: '{topic}'.\n"
        "Here is the context from past conversations:\n"
        "{context}\n\n"
        "Specifically, find supplemental information that is not available in the private documents. "
        "The past conversation context can help you understand what kind of supplemental "
        "information the user might be looking for."
    ),
    expected_output = "A summary of the most relevant, up-to-date information from your web search.",
    agent = general_researcher
)