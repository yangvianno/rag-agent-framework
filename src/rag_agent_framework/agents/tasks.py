# src/rag_agent_framework/agents/tasks.py -- Agent Task Definitions

from crewai import Task
from .research_agents import document_researcher, general_researcher

# Task for Document Research agent
document_researcher_task = Task(
    description = (
        "Answer the user's questions based on the document knowledge base."
        "Use the 'Document Knowledge Base Tool' to find the information."
    ),
    expected_output = "A clear and concise asnwer to the user's question, based solely on the information found in the documents.",
    agent = document_researcher
)

general_researcher_task = Task(
    description = (
        "Answer the user's question by searching the web."
        "If the question is general or queries up-to-date information, use this task."
    ),
    expected_output = "A clear and consise answer to the user's question, based on information on the web.",
    agent = general_researcher
)