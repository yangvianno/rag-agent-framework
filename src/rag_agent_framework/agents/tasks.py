# src/rag_agent_framework/agents/tasks.py -- Agent Task Definitions

from crewai import Task
from .research_agents import document_researcher, general_researcher, report_writer

# Task 1: Search the internal documents
document_research_task = Task(
    description = "Search the user's private documents for information related to the topic: '{topic}'.",
    expected_output = "A summary of the findings from the documents. If no relevant information is found, state that clearly.",
    agent = document_researcher
)

# Task 2: Search the web
web_research_task = Task(
    description = "Search the public web for up-to-date information on the topic: '{topic}'.",
    expected_output = "A summary of the key findings from the web search.",
    agent = general_researcher
)

# Task 3: Write the final report
writer_task = Task(
    description = (
        "Review the research findings from both the DocumentResearcher and the GeneralResearcher. "
        "Your job is to synthesize this information into a single, cohesive final report. "
        "It is critical that you address the user's original question: '{topic}'. "
        "Explicitly mention if the internal documents contained relevant information or not. "
        "Then, present the web findings to provide a complete answer."
    ),
    expected_output = "A final, comprehensive report that synthesizes all research findings and directly answers the user's original question.",
    agent = report_writer,
    # Context is the output of the previous two tasks
    context = [document_research_task, web_research_task]
)