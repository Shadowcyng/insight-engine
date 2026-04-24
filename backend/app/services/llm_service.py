from groq import Groq
from app.core.config import settings

class LLMModel:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def get_response(self, messages, **kwargs ):
        try:
            request_args = {
            "messages": messages,
            "model": "llama-3.1-8b-instant",
            "temperature": 0.2,
            }
            # Overwrite default args or add new ones (like tools, tool_choice)
            request_args.update(kwargs)

            chat_completion = self.client.chat.completions.create(**request_args)
            return chat_completion.choices[0].message
        except Exception as e:
            raise e
# Usage
llm = LLMModel(api_key=settings.AI_API_KEY)
