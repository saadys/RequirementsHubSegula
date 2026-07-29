import litellm
from litellm import Router
from langchain_litellm import ChatLiteLLMRouter
from backend import config

model_list = []

if config.GEMINI_API_KEY_1:
    model_list.append({
        "model_name": "gemini-model-group",
        "litellm_params": {
            "model": config.PRIMARY_MODEL,
            "api_key": config.GEMINI_API_KEY_1,
        }
    })

if config.GEMINI_API_KEY_2:
    model_list.append({
        "model_name": "gemini-model-group",
        "litellm_params": {
            "model": config.PRIMARY_MODEL,
            "api_key": config.GEMINI_API_KEY_2,
        }
    })

if config.OPENAI_API_KEY:
    model_list.append({
        "model_name": "openai-fallback",
        "litellm_params": {
            "model": config.FALLBACK_MODEL,
            "api_key": config.OPENAI_API_KEY,
        }
    })

if not model_list:
    model_list.append({
        "model_name": "gemini-model-group",
        "litellm_params": {
            "model": config.PRIMARY_MODEL,
            "api_key": "dummy-key",
        }
    })

# Initialize LiteLLM Router with fallback behavior
router = Router(
    model_list=model_list,
    fallbacks=[{"gemini-model-group": ["openai-fallback"]}] if config.OPENAI_API_KEY else [],
)

def get_llm() -> ChatLiteLLMRouter:
    """Returns a ChatLiteLLMRouter instance with multi-key and fallback support."""
    return ChatLiteLLMRouter(
        router=router,
        model="gemini-model-group",
        temperature=config.LLM_TEMPERATURE,
    )

