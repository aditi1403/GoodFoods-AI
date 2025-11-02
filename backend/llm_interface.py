# backend/llm_interface.py
import subprocess, json, os, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def query_llm(prompt: str, model: str = None) -> str:
    model = model or OLLAMA_MODEL
    cmd = ["ollama", "run", model, prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error("Ollama call failed: %s", e.stderr)
        return ""

def query_llm_json(prompt: str, model: str = None):
    """
    Instruct the model to return JSON; if parsing fails, return raw text under "raw".
    Use concise system prompt wrappers when calling from middleware.
    """
    raw = query_llm(prompt, model)
    try:
        return json.loads(raw)
    except Exception:
        logger.warning("LLM response not valid JSON. Returning {'raw': ...}")
        return {"raw": raw}
