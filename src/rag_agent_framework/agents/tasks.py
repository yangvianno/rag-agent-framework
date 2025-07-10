# src/rag_agent_framework/agents/tasks.py -- Agent Task Definitions

from crewai import Task
from .research_agents import document_researcher, general_researcher, manager_agent

document_researcher_task = Task(
    description = (
         "You have been assigned a research task: '{topic}'.\n"
        "Here is the context from past conversations if available: {context}\n\n"
        "Your primary goal is to use the 'Document Knowledge Base Tool' to find the answer "
        "exclusively within the provided documents. You MUST use this tool. "
        "Produce a detailed, final answer based on your findings."
    ),
    expected_output = (
        "A detailed, final report based *only* on the information found in the documents. "
        "If no relevant information is found, explicitly state that."
    ),
    agent = document_researcher,
)

general_researcher_task = Task(
    description = (
        "You have been assigned a research task: '{topic}'.\n"
        "Here is the context from past conversations if available: {context}\n\n"
        "Your primary goal is to use your search tools to find information on the web. "
        "Produce a detailed, final answer based on your findings."
    ),
    expected_output = "A comprehensive, final report summarizing the most relevant information from your web search.",
    agent = general_researcher,
)

# --- Manager Task --- This is entry point task that the manager will handle
manager_task = Task(
    description = (
        "Analyze the user's research topic: '{topic}'. Your ONLY job is to determine the best specialist agent for the task and delegate the work to them. "
        "If the topic involves comparing information against internal documents, delegate to the 'Document Researcher'. "
        "If the topic requires external, up-to-the-minute information, delegate to the 'General Researcher'. "
        "Do not answer the question yourself."
    ),
    expected_output = "The final, detailed research report compiled by the specialist agent (either the Document Researcher or General Researcher).",
    agent = manager_agent
)