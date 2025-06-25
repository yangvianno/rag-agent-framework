# src/rag_agent_framework/core/config.py

import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# 1. Load environment variables from .env (at repo root)
#    core/ → rag_agent_framework/ → src/ → project root
base_dir = Path(__file__).resolve().parents[3]
load_dotenv(dotenv_path = base_dir / ".env")        # Loads /../../.env

# 2. Reads config/config.yaml once into _cfg
config_path = base_dir / "config" / "config.yaml"
if not config_path.is_file(): 
    raise FileNotFoundError(f"Config file not found at {config_path}")
with open(config_path, "r") as f:
    _cfg = yaml.safe_load(f)

# 3. Expose config sections
VECTOR_DB_CFG = _cfg.get("vector_db", {})
LLM_CFG       = _cfg.get("llm", {})
AGENT_CFG     = _cfg.get("agent", {})
RETRIEVER_K   = _cfg.get("retriever", {}).get("k", 4)

# 4. Pull keys from environment
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = LLM_CFG.get("openai", {}).get("embedding_model") # will return None instead of LLM_CFG["openai"]["embedding_model"]
OLLAMA_URL         = os.getenv("OLLAMA_URL")
# QDRANT_URL         = os.getenv("QDRANT_URL") Get the URL from the environment in the scripts/ingest.py
SERPAPI_API_KEY    = os.getenv("SERPAPI_API_KEY")

