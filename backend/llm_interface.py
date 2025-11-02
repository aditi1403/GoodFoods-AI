import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO)

def query_llm(prompt: str, model: str = "llama3") -> str:
    pass


if __name__ == "__main__":
    prompt = ""
    reply = query_llm(prompt)
    print(reply)