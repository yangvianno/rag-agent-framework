# scripts/chat.py -- will be an interactive command-line chat with memory that:
"""
    1. Remembers who you are.

    2. Retrieves past conversations before answering a new question.

    3. Saves a summary of the new conversation for the future.
"""

import os
import sys
from pathlib import Path

from rag_agent_framework.utils import path_fix # noqa: F401
from rag_agent_framework.rag.memory import MemoryStore, get_summarizer
from rag_agent_framework.agents.crew import agent_crew

def main():
    """An interactive chat loop that uses the agentic crew and long-term memory"""
    # Use a fized user_id for this session. In real app needs user login
    user_id = "cli_user_alex"
    print(f"Welcome! Your user ID for this session is: '{user_id}'")
    print("Type 'exit' to end the conversation.")
    print("-" * 100)

    # Initialize the memory store and summarizer
    memory = MemoryStore(user_id=user_id)
    summarizer = get_summarizer()

    # Start the interactive chat loop
    while True:
        question = input("You: ")
        if question.lower() == 'exit':
            print("Ending chat. Good bye!")
            break

        # 1. Retrieve relevant memories
        past_memories = memory.get_memories(query=question, k=5)
        past_memories_str = "\n".join([mem.page_content for mem in past_memories])

        # 2. Prepare the inputs for the crew
        inputs = {
            "topic": question,
            "context": f"Relevant past conversations:\n{past_memories_str}"
        }

        # 3. Run the crew
        print("\n🤖 Crew is thinking...")
        result = agent_crew.kickoff(inputs=inputs)
        print("\nAgent:", result)
        print("-" * 100)

        # 4. Summarize and store the new interaction
        conversation_to_summarize = f"User asked: {question}\nAgent answered: {result}"
        summary = summarizer.invoke({"text": conversation_to_summarize})

        # 5. Call the add_memory method on the memory instance
        memory.add_memory(summary.content)

if __name__ == "__main__":
    main()