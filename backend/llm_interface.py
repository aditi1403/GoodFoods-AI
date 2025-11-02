import subprocess, json, os, logging, re
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

def safe_parse_response(response_text: str):
    """
    Try to parse valid JSON; if invalid, sanitize and retry.
    Returns dict or {'raw': ...}
    """
    if not response_text:
        return {"raw": ""}
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Extract JSON substring if model added extra text
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                cleaned = match.group(0)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
        # Last fallback: strip code blocks, try again
        cleaned = (
            response_text.replace("```json", "")
            .replace("```", "")
            .strip()
        )
        try:
            return json.loads(cleaned)
        except Exception:
            logger.warning("LLM response not valid JSON. Returning {'raw': ...}")
            return {"raw": response_text}

def query_llm_json(prompt: str, model: str = None):
    """
    Force the model to return valid JSON.
    """
    raw = query_llm(prompt, model)
    return safe_parse_response(raw)
