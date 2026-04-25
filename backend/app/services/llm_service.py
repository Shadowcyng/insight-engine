from groq import Groq
from app.core.config import settings
import structlog

log = structlog.get_logger()

class LLMModel:
    def __init__(self, api_key):
        log.info("initializing_llm_model", model="llama-3.1-8b-instant")
        self.client = Groq(api_key=api_key)

    def get_response(self, messages, **kwargs ):
        log.info("llm_get_response_called", message_count=len(messages), model="llama-3.1-8b-instant")
        try:
            request_args = {
            "messages": messages,
            "model": "llama-3.1-8b-instant",
            "temperature": 0.2,
            }
            # Overwrite default args or add new ones (like tools, tool_choice)
            request_args.update(kwargs)
            
            log.debug("sending_request_to_groq_api", has_tools="tools" in kwargs, has_tool_choice="tool_choice" in kwargs)

            chat_completion = self.client.chat.completions.create(**request_args)
            log.debug("groq_api_response_received", choice_count=len(chat_completion.choices))
            log.info("llm_response_generated_successfully")
            return chat_completion.choices[0].message
        except Exception as e:
            log.error("llm_get_response_failed", error=str(e), message_count=len(messages))
            raise

# Usage
llm = LLMModel(api_key=settings.AI_API_KEY)
