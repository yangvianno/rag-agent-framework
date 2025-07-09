# ui/app.py --  Streamlit app with web-based chat interface for users

import streamlit
import requests
import uuid

# --- Configuration ---
# This should point to the FastAPI server running in the Docker. Since the Streamlit app runs on the host, we use local host.
API_URL = "http://localhost:8000/chat"


# --- UI Setup ---
streamlit.set_page_config(page_title = "🤖 RAG Agent UI", layout = "wide")
streamlit.title("🤖 RAG + Agentic AI Framework")
streamlit.markdown("Interact with the agent crew. The backend manages document ingestion and memory")


# --- Session State Initialization ---
# Initialize a unique user_id for the session and the chat history
if "user_id" not in streamlit.session_state:
    streamlit.session_state.user_id = f"web_user_{str(uuid.uuid4())[:8]}"
    streamlit.session_state.message = []

# Display the user ID in the sidebar for reference
streamlit.sidebar.info(f"Your User ID for this session is:\n'{streamlit.session_state.user_id}'")
streamlit.markdown(
    """
        **How to Use:**
        1. First, run the backend services using `docker-compse up`
        2. Next, ingest documents using the `scripts/ingest.py` script from the terminal
            ```bash
            # From your project root
            QDRANT_URL="http://localhost:6333" poetry run python scripts/ingest.py -s data/your_file.pdf
            ```
        3. Once ingested, ask questions about the document in the chat window
    """
)


# --- Display Chat History ---
# Render previous messages from the session state
for message in streamlit.session_state.messages:
    with streamlit.chat_message(message["role"]):
        streamlit.markdown(message["content"])


# --- Handle User Input ---
if prompt := streamlit.chat_input("Ask a question about your documents.."):
    # Add user message to chat history and display it
    streamlit.session_state.messaages.append({"role": "user", "content": prompt})
    with streamlit.chat_message("user"):
        streamlit.markdown(prompt)

    # Get and display assitant response
    with streamlit.chat_message("assistant"):
        message_placeholder = streamlit.empty()

        with streamlit.spinner("The agent crew is thinking..."):
            try:
                # Prepare the request payload for the API
                payload = {
                    "question": prompt,
                    "user_id": streamlit.session_state.user_id
                }

                # Send the request to the FastAPI server
                response = requests.post(API_URL, json=payload, timeout=300)
                response.raise_for_status()     # Raise an exception for bad status code (4xx or 5xx)

                response_data = response.json()
                full_response = response_data.get("answer", "Sorry, I encountered an issue and received no answer.")

                # Optionally display the memory summary in a expander
                if summary := response_data.get("memory_summary"):
                    with streamlit.explander("📝 View Memory Summary"):
                        streamlit.write(summary)

            except requests.exceptions.RequestException as e:
                full_response = f"**Error:** Could not connect to the API. Please ensure the backend services are running. \n\nDetails: {e}"
            except Exception as e:
                full_response = f"**An unexpected error occurred:** {e}"

        message_placeholder.markdown(full_response)

    # Add the assistant's reponse to the chat history
    streamlit.session_state.messages.append({"role": "assistant", "content": full_response})