
import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


load_dotenv()

MODEL = "gpt-4.1-mini"


def get_system_prompt(language="ru"):
    """Return Emily's system instructions in the selected language."""

    if language == "en":
        return """
You are Emily, a professional AI real estate assistant.

You help users explore residential properties in the United States.

Rules:
- Communicate naturally and professionally in English.
- Help users understand their property search requirements.
- Never invent property listings, prices, addresses, or availability.
- The application's property catalogue is the only source of property data.
- If you do not have verified information, say so clearly.
- Do not claim that demo properties are real listings.
- Be concise, helpful, and transparent.
"""

    return """
Ты Emily, профессиональный AI-помощник по недвижимости.

Ты помогаешь пользователям подбирать жилую недвижимость в США.

Правила:
- Общайся естественно и профессионально на русском языке.
- Помогай уточнять требования к недвижимости.
- Никогда не выдумывай объявления, цены, адреса или наличие объектов.
- Каталог приложения является единственным источником данных об объектах.
- Если проверенной информации нет, честно сообщи об этом.
- Не выдавай демонстрационные объекты за реальные объявления.
- Отвечай понятно, кратко и доброжелательно.
"""


def get_openai_client():
    """Create an OpenAI client using the environment API key."""

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Check your .env configuration."
        )

    return OpenAI(api_key=api_key)


def generate_ai_response(message, history=None, language="ru"):
    """Generate an AI response using the OpenAI Responses API."""

    history = history or []

    conversation = []

    for item in history[-10:]:
        role = item.get("role")
        content = item.get("content")

        if role in ("user", "assistant") and isinstance(content, str):
            conversation.append({
                "role": role,
                "content": content
            })

    conversation.append({
        "role": "user",
        "content": message
    })

    try:
        client = get_openai_client()

        response = client.responses.create(
            model=MODEL,
            instructions=get_system_prompt(language),
            input=conversation,
            max_output_tokens=350,
        )

        return response.output_text.strip()

    except OpenAIError:
        return (
            "Не удалось получить ответ от AI-сервиса. Попробуйте ещё раз."
            if language != "en"
            else "The AI service could not generate a response. Please try again."
        )

    except RuntimeError:
        return (
            "AI-сервис пока не настроен. Проверьте конфигурацию приложения."
            if language != "en"
            else "The AI service is not configured. Please check the application settings."
        )


