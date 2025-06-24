# src/rag_agent_framework/core/config.py

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 1. Load environment variables from .env (at repo root)
base_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path = base_dir / ".env")        # Finds /../../.env

# 2. Reads config/config.yaml once into _cfg
config_path = base_dir / "config" / "config.yaml"
with open(config_path, "r") as f:
    _cfg = yaml.safe_load(f)

# 3. Expose constants
VECTOR_DB_CFG = _cfg["vector_db"]
LLM_CFG       = _cfg["llm"]
AGENT_CFG     = _cfg["agent"]
RETRIEVER_K   = _cfg["retriever"]

# 4. Pull keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_URL     = os.getenv("OLLAMA_URL")
QDRANT_URL     = os.getenv("QDRANT_URL")
SERPAPI_API_KEY= os.getenv("SERPAPI_API_KEY")

