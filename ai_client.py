import json
import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from tools import TOOLS, execute_tool


load_dotenv()

MODEL = "gpt-4.1-mini"
MAX_TOOL_ROUNDS = 3


def get_system_prompt(language="ru"):
    """Return Emily's system instructions in the selected language."""

    if language == "en":
        return """
You are Emily, a professional AI real estate assistant.

You help users explore residential properties in the United States.

Rules:
- Communicate naturally and professionally in English.
- Help users understand their property search requirements.
- Use the search_properties tool when users ask to find properties.
- Use the recommend_properties tool when users ask for recommendations.
- Never invent property listings, prices, addresses, or availability.
- Property information returned by tools is the only source of catalogue data.
- Clearly explain when the catalogue has no matching properties.
- Do not claim that demo properties are real listings.
- Ask a clarifying question when essential search information is missing.
- Be concise, helpful, and transparent.
"""

    return """
Ты Emily, профессиональный AI-помощник по недвижимости.

Ты помогаешь пользователям подбирать жилую недвижимость в США.

Правила:
- Общайся естественно и профессионально на русском языке.
- Помогай уточнять требования к недвижимости.
- Если пользователь ищет объекты, используй инструмент search_properties.
- Если пользователь просит рекомендации, используй recommend_properties.
- Никогда не выдумывай объявления, цены, адреса или наличие объектов.
- Информация, возвращённая инструментами, является единственным источником данных каталога.
- Если подходящих объектов нет, сообщи об этом честно.
- Не выдавай демонстрационные объекты за реальные объявления.
- Если для рекомендации не хватает важных требований, задай уточняющий вопрос.
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


def _build_conversation(message, history=None):
    """Prepare a safe conversation history for the Responses API."""

    conversation = []

    for item in (history or [])[-10:]:
        role = item.get("role")
        content = item.get("content")

        if role in ("user", "assistant") and isinstance(content, str):
            conversation.append({
                "role": role,
                "content": content,
            })

    conversation.append({
        "role": "user",
        "content": message,
    })

    return conversation



def _run_tool_calls(response, conversation, properties, client, language):
    """Execute model-requested tools and return structured results."""

    input_items = list(conversation)
    tool_result = None

    for round_index in range(MAX_TOOL_ROUNDS + 1):
        function_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if not function_calls:
            answer = response.output_text.strip()

            if tool_result is not None:
                tool_result["content"] = answer
                return tool_result

            return answer

        if round_index >= MAX_TOOL_ROUNDS:
            return (
                "Не удалось завершить обработку запроса. Попробуйте уточнить вопрос."
                if language != "en"
                else "The request could not be completed. Please clarify your question."
            )

        input_items.extend(response.output)
        tool_outputs = []

        for call in function_calls:
            try:
                arguments = json.loads(call.arguments)

                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")

                result = execute_tool(
                    name=call.name,
                    arguments=arguments,
                    properties=properties,
                )

                parsed_result = json.loads(result)

                if "error" not in parsed_result:
                    tool_result = {
                        "kind": (
                            "property_recommendation"
                            if call.name == "recommend_properties"
                            else "property_results"
                        ),
                        "content": "",
                        "properties": parsed_result.get("results", []),
                        "total": parsed_result.get("count", 0),
                        "tool_name": call.name,
                    }

                    if call.name == "recommend_properties":
                        tool_result["budget"] = arguments.get("budget")

            except (json.JSONDecodeError, ValueError, TypeError) as error:
                result = json.dumps(
                    {"error": str(error)},
                    ensure_ascii=False,
                )

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": result,
            })

        input_items.extend(tool_outputs)

        response = client.responses.create(
            model=MODEL,
            instructions=get_system_prompt(language),
            input=input_items,
            tools=TOOLS,
            max_output_tokens=350,
        )

    return (
        "Не удалось завершить обработку запроса. Попробуйте уточнить вопрос."
        if language != "en"
        else "The request could not be completed. Please clarify your question."
    )


def generate_ai_response(
    message,
    history=None,
    language="ru",
    properties=None,
):
    """Generate an AI response with optional property function calling."""

    conversation = _build_conversation(message, history)

    try:
        client = get_openai_client()

        if properties is not None:
            response = client.responses.create(
                model=MODEL,
                instructions=get_system_prompt(language),
                input=conversation,
                tools=TOOLS,
                max_output_tokens=350,
            )

            return _run_tool_calls(
                response=response,
                conversation=conversation,
                properties=properties,
                client=client,
                language=language,
            )

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
