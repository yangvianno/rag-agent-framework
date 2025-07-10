# src/rag_agent_framework/agents/research_agents.py -- Agent Definitions, define their tasks, and assembling them into a crew
# document_researcher -- uses the RAG tool
# general_researcher -- search 

import os
from crewai import Agent
from crewai_tools import DuckDuckGoSearchRun
search_tool = DuckDuckGoSearchRun()     # Instantiate the tool

from langchain_openai import ChatOpenAI
from langchain_community.chat_models.ollama import ChatOllama

from rag_agent_framework.tools.rag_tool import rag_tool
from rag_agent_framework.core.config import LLM_CFG, OPENAI_API_KEY, OLLAMA_URL

# Get the LLM for the agents
def get_agent_llm():
    if LLM_CFG["default"] == "openai":
        return ChatOpenAI(
            model = LLM_CFG["openai"]["chat_model"],
            openai_api_key = OPENAI_API_KEY
        )
    else:
        return ChatOllama(
            model = LLM_CFG["ollama"]["chat_model"],
            base_url = OLLAMA_URL
        )
    
# --- Researcher Agent --- uses the RAG tool
document_researcher = Agent(
    role = "DocumentResearcher",
    goal = "Find and return relevant information from the provided documents.",
    backstory = "You are an expert at searching and extracting information from a document knowledge base. You are known for your ability to find the most relevant and accurate information quickly.",
    tools = [rag_tool],
    llm = get_agent_llm(),
    allow_delegation = False,   # In the CrewAI framework, an Agent can (optionally) delegate tasks to other agents.
    verbose = True,
)

# --- General Researcher Agent --- search the web, uses SERPAPI_API_KEY in the .env file
general_researcher = Agent(
    role = "GeneralResearcher",
    goal = "Find and return general information from the web.",
    backstory = "You are an expert web researcher, skilled at using search engines to find accurate and up-to-date information at any topic.",
    tools = [search_tool],
    llm = get_agent_llm(),
    allow_delegation = False,   # In the CrewAI framework, an Agent can (optionally) delegate tasks to other agents.
    verbose = True
)

# --- Writer Agent --- synthesizes findings from other agents into a final report.
report_writer = Agent(
    role = "ReportWriter",
    goal = "Write a clear, concise, and accurate summary report based on the research findings provided by other agents.",
    backstory = "You are an expert technical writer, known for your ability to synthesize complex information from multiple sources into a perfectly formatted and easy-to-understand report that directly answers the user's original question.",
    llm = get_agent_llm(),
    allow_delegation = False,
    verbose = True
)