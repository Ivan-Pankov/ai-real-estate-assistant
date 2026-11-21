import json
from pathlib import Path

from tools import execute_tool


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "properties.json"


def load_properties():
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def test_search_properties_tool():
    result = execute_tool(
        "search_properties",
        {"query": "Дом в Майами до $500,000"},
        load_properties(),
    )

    data = json.loads(result)

    assert data["count"] > 0
    assert data["results"]
    assert all(item["city"] == "Miami" for item in data["results"])


def test_recommend_properties_tool():
    result = execute_tool(
        "recommend_properties",
        {
            "budget": 500000,
            "min_bedrooms": 3,
            "limit": 3,
        },
        load_properties(),
    )

    data = json.loads(result)

    assert data["count"] > 0
    assert len(data["results"]) <= 3
    assert all(item["price"] <= 500000 for item in data["results"])
    assert all(item["bedrooms"] >= 3 for item in data["results"])


def test_tool_rejects_invalid_budget():
    result = execute_tool(
        "recommend_properties",
        {
            "budget": -100,
            "min_bedrooms": 2,
            "limit": 3,
        },
        load_properties(),
    )

    data = json.loads(result)

    assert "error" in data


def test_tool_rejects_unknown_name():
    result = execute_tool(
        "unknown_tool",
        {},
        load_properties(),
    )

    data = json.loads(result)

    assert "error" in data
