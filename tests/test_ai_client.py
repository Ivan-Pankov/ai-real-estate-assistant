import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from ai_client import _run_tool_calls


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "properties.json"


def load_properties():
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def make_function_call(name, arguments):
    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=json.dumps(arguments),
        call_id="test_call_001",
    )


def make_response(output=None, output_text=""):
    return SimpleNamespace(
        output=output or [],
        output_text=output_text,
    )


def test_search_function_call_cycle():
    properties = load_properties()

    initial_response = make_response(
        output=[
            make_function_call(
                "search_properties",
                {"query": "Дом в Майами до $500,000"},
            )
        ]
    )

    final_response = make_response(
        output_text="Найдено два подходящих дома."
    )

    client = Mock()
    client.responses.create.return_value = final_response

    result = _run_tool_calls(
        response=initial_response,
        conversation=[{"role": "user", "content": "Find a house in Miami"}],
        properties=properties,
        client=client,
        language="ru",
    )

    assert result["tool_name"] == "search_properties"
    assert result["kind"] == "property_results"
    assert result["total"] == 2
    assert result["content"] == "Найдено два подходящих дома."
    assert client.responses.create.call_count == 1


def test_recommendation_function_call_cycle():
    properties = load_properties()

    initial_response = make_response(
        output=[
            make_function_call(
                "recommend_properties",
                {
                    "budget": 500000,
                    "min_bedrooms": 3,
                    "limit": 3,
                },
            )
        ]
    )

    final_response = make_response(
        output_text="Рекомендую первый вариант."
    )

    client = Mock()
    client.responses.create.return_value = final_response

    result = _run_tool_calls(
        response=initial_response,
        conversation=[{"role": "user", "content": "Recommend a house"}],
        properties=properties,
        client=client,
        language="ru",
    )

    assert result["tool_name"] == "recommend_properties"
    assert result["kind"] == "property_recommendation"
    assert result["budget"] == 500000
    assert result["total"] > 0
    assert all(item["price"] <= 500000 for item in result["properties"])
    assert result["content"] == "Рекомендую первый вариант."


def test_response_without_function_call():
    response = make_response(output_text="Здравствуйте! Чем могу помочь?")

    result = _run_tool_calls(
        response=response,
        conversation=[],
        properties=load_properties(),
        client=Mock(),
        language="ru",
    )

    assert result == "Здравствуйте! Чем могу помочь?"
