# src/rag_agent_framework/core/config.py -- Centralization and a Single Source of Truth 🏛️ got configuration

import os, yaml
from pathlib import Path
from dotenv  import load_dotenv
from box     import Box

# 1. Load environment variables from .env at project root
#    core/ → rag_agent_framework/ → src/ → project root
base_dir = Path(__file__).resolve().parents[3]
load_dotenv(dotenv_path = base_dir / ".env")        # Loads /../../.env

# 2. Load the main configuration file -- Reads config/config.yaml once into _cfg
config_path = base_dir / "config" / "config.yaml"
if not config_path.is_file(): 
    raise FileNotFoundError(f"Config file not found at {config_path}")
with open(config_path, "r") as f:
    _cfg = yaml.safe_load(f)

# 3. Expose config sections as constants        <- config.yaml
VECTOR_DB_CFG = _cfg.get("vector_db", {})
LLM_CFG       = _cfg.get("llm", {})
AGENT_CFG     = _cfg.get("agent", {})
RETRIEVER_CFG = _cfg.get("retriever", {})

# 4. Pull keys from environment                 <- .env
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = LLM_CFG.get("openai", {}).get("embedding_model") # will return None instead of LLM_CFG["openai"]["embedding_model"]
OLLAMA_URL         = os.getenv("OLLAMA_URL")
QDRANT_URL         = os.getenv("QDRANT_URL")
SERPAPI_API_KEY    = os.getenv("SERPAPI_API_KEY")
MAX_UPLOAD_SIZE    = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")) * (1 << 20)

# Create a importable object                    -> config.py
config = Box(_cfg)