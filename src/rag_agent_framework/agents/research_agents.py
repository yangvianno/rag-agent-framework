# src/rag_agent_framework/agents/research_agents.py -- Agent Definitions, define their tasks, and assembling them into a crew
# document_researcher -- uses the RAG tool
# general_researcher -- search 

import os
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_community.chat_models.ollama import ChatOllama

from rag_agent_framework.tools.rag_tool import rag_tool
from rag_agent_framework.core.config import LLM_CFG

# Get the LLM for the agents
def get_agent_llm():
    if LLM_CFG["default"] == "openai":
        return ChatOpenAI(
            model = LLM_CFG["openai"]["chat_model"],
            openai_api_key = os.getenv("OPENAI_API_KEY")
        )
    else:
        return ChatOllama(
            model = LLM_CFG["ollama"]["model"],
            base_url = os.getenv("OLLAMA_URL")
        )
    
# Create a researcher agent that uses the RAG tool
document_researcher = Agent(
    role = "Document Researcher",
    goal = "Find and return relevant information from the provided documents.",
    backstory = "You are an expert at searching and extracting information from a document knowledge base. You are known for your ability to find the most relevant and accurate information quickly.",
    tools = [rag_tool],
    llm = get_agent_llm(),
    allow_delegation = False,   # In the CrewAI framework, an Agent can (optionally) delegate tasks to other agents.
    verbose = True,
)

# Create a general researcher agent that can search the web
# This agent uses SERPAPI_API_KEY in the .env file
general_researcher = Agent(
    role = "General Researcher",
    goal = "Find and return general information from the web.",
    backstory = "You are an expert web researcher, skilled at using search engines to find accurate and up-to-date information at any topic.",
    # This agent will have a web search tool added to it automatically by CrewAI
    llm = get_agent_llm(),
    allow_delegation = False,   # In the CrewAI framework, an Agent can (optionally) delegate tasks to other agents.
    verbose = True
)

# --- Manager Agent ---
# This agent will delegate tasks to the appropriate researcher
manager_agent = Agent(
    role = "Project Manager",
    goal = "Efficiently manage the research process by delegating tasks to the appropriate specialist agent. Review the final answers to ensure they are complete and meet the user's meet.",
    backstory = "You are an experienced project manager, skilled at analyzing requests and identifying the best person for the job. You break down complex questions and ensure that final product from your team is coherent and valuable.",
    llm = get_agent_llm(),
    allow_delegation = True,
    verbose = True
)