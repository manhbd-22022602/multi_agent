import yaml
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain.chat_models import init_chat_model

# Load YAML config
CONFIG_PATH = Path(__file__).parent / "base.yml"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    _cfg = yaml.safe_load(f)

# Biến tĩnh
AVAILABLE_AGENTS: dict[str, str] = _cfg["available_agents"]
LOCAL_LLM_NAME = _cfg["local_llm_model"]
LOCAL_LLM_URL = _cfg["local_llm_url"]
API_LLM_NAME = _cfg["api_llm_model"]
TEMPERATURE = _cfg["llm_temperature"]

# Hàm load model
def load_chat_model(fully_specified_name: str, temperature: float = 0) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider, temperature=temperature)

# Load 2 model
llm_local: BaseChatModel = load_chat_model(LOCAL_LLM_NAME)
llm_api:   BaseChatModel = load_chat_model(API_LLM_NAME, TEMPERATURE)
